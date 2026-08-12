#!/usr/bin/env python3
"""Safe, low-volume negative edge tests. Dry-run unless --execute is supplied.

This is not a load test, vulnerability scanner, brute-force tool or DDoS simulator.
It sends at most a handful of requests designed to validate policy behavior.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
import urllib.error
import urllib.parse
import urllib.request


PROBES = [
    ("suspicious-user-agent", "/", {"User-Agent": "sqlmap-safe-edge-validation"}),
    ("sqli-query", "/?edge_test=" + urllib.parse.quote("1' OR '1'='1"), {"User-Agent": "ClearGlass-Edge-Test/1.0"}),
    ("xss-query", "/?edge_test=" + urllib.parse.quote("<script>alert(1)</script>"), {"User-Agent": "ClearGlass-Edge-Test/1.0"}),
    ("path-traversal", "/%2e%2e/%2e%2e/.env", {"User-Agent": "ClearGlass-Edge-Test/1.0"}),
    ("scanner-path", "/.git/config", {"User-Agent": "ClearGlass-Edge-Test/1.0"}),
    ("oversized-header-bounded", "/", {"User-Agent": "ClearGlass-Edge-Test/1.0", "X-Edge-Test-Padding": "A" * 9000}),
    ("oversized-url-bounded", "/?edge_size_probe=" + "A" * 17000, {"User-Agent": "ClearGlass-Edge-Test/1.0"}),
]


def validate_url(value: str, label: str) -> str:
    if len(value) > 2048:
        raise ValueError(f"{label} is too long")
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{label} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError(f"{label} must not contain credentials or a fragment")
    return value


def send(url: str, headers: dict[str, str]) -> tuple[int, dict[str, str], bytes]:
    req = urllib.request.Request(url, method="GET", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read(1024 * 1024)
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read(64 * 1024)
    except urllib.error.URLError as exc:
        return 0, {}, str(exc.reason).encode("utf-8", errors="replace")


def classify(status: int, headers: dict[str, str]) -> str:
    if status == 429:
        return "rate-limited"
    if status in {401, 403}:
        if "cf-mitigated" in headers or "cf-ray" in headers:
            return "blocked-or-challenged-at-edge"
        return "denied"
    if 200 <= status < 400:
        return "allowed"
    return f"status-{status}"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--execute", action="store_true", help="Send the safe low-volume probes.")
    mode.add_argument("--dry-run", action="store_true", help="Print probes only (default).")
    parser.add_argument("--origin-url", default="", help="Optional known origin URL to check for direct reachability.")
    parser.add_argument("--expect-origin-private", action="store_true", help="Fail when --origin-url is directly reachable. Do not use for GitHub Pages.")
    parser.add_argument("--expect-enforcement", action="store_true", help="Fail when high-signal negative probes are allowed. Use only after a reviewed enforce rollout.")
    parser.add_argument("--rate-probe-count", type=int, default=3, help="Ordinary repeated GETs; capped at 20.")
    args = parser.parse_args()

    try:
        base = validate_url(args.base_url, "base URL").rstrip("/")
        origin_url = validate_url(args.origin_url, "origin URL") if args.origin_url else ""
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    execute = args.execute
    rate_count = min(max(args.rate_probe_count, 1), 20)
    failures: list[str] = []
    if (args.expect_enforcement or args.expect_origin_private) and not execute:
        print("ERROR: expectation flags require --execute", file=sys.stderr)
        return 2
    if args.expect_origin_private and not origin_url:
        print("ERROR: --expect-origin-private requires --origin-url", file=sys.stderr)
        return 2

    print("Mode:", "EXECUTE (safe low volume)" if execute else "DRY RUN")
    print("This tool never performs credential stuffing, destructive payloads, port scans or DDoS simulation.")

    for name, path, headers in PROBES:
        url = base + path
        if not execute:
            print(f"PLAN {name}: GET {base}{path[:120]}; url_bytes={len(url.encode())}; headers={list(headers)}")
            continue
        status, response_headers, _ = send(url, headers)
        print(f"RESULT {name}: {status} {classify(status, response_headers)} ray={response_headers.get('cf-ray', 'n/a')}")
        if args.expect_enforcement and name in {"suspicious-user-agent", "sqli-query", "xss-query", "path-traversal", "scanner-path"} and 200 <= status < 400:
            failures.append(f"{name} was allowed while --expect-enforcement was set")

    if not execute:
        print(f"PLAN rate-behavior: {rate_count} ordinary GET requests to {base}/ (well below DDoS/load-test levels)")
        print(f"PLAN cache-poisoning: two GET requests to {base}/?edge_cache_probe=bounded-v1; first uses X-Forwarded-Host, second is clean")
    else:
        results = []
        for _ in range(rate_count):
            status, response_headers, _ = send(base + "/", {"User-Agent": "ClearGlass-Edge-Rate-Probe/1.0"})
            results.append(classify(status, response_headers))
        print("RESULT rate-behavior:", ", ".join(results))

        poison_url = base + "/?edge_cache_probe=bounded-v1"
        poison_status, _, poison_body = send(
            poison_url,
            {"User-Agent": "ClearGlass-Edge-Test/1.0", "X-Forwarded-Host": "invalid.example"},
        )
        clean_status, clean_headers, clean_body = send(
            poison_url,
            {"User-Agent": "ClearGlass-Edge-Test/1.0"},
        )
        same_body = hashlib.sha256(poison_body).digest() == hashlib.sha256(clean_body).digest()
        print(
            "RESULT cache-poisoning: "
            f"poison_status={poison_status} clean_status={clean_status} same_body={same_body} "
            f"cache={clean_headers.get('cf-cache-status', 'n/a')}"
        )
        if 200 <= poison_status < 400 and 200 <= clean_status < 400 and not same_body:
            failures.append("cache-poisoning probe changed the subsequent clean response")

    if origin_url:
        if not execute:
            print(f"PLAN origin-exposure: single GET {origin_url}")
        else:
            status, _, _ = send(origin_url, {"User-Agent": "ClearGlass-Origin-Exposure-Check/1.0"})
            print(f"RESULT origin-exposure: {status}; direct reachability is a known GitHub Pages limitation if successful")
            if args.expect_origin_private and 200 <= status < 400:
                failures.append("origin is directly reachable but --expect-origin-private was set")

    print("NOT SIMULATED: country/ASN source location, verified crawler identity, trusted-IP exception, signed webhook identity, credential stuffing, or provider-scale DDoS. Validate those with provider analytics/staging sources, not spoofed headers.")
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
