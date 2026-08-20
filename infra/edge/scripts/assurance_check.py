#!/usr/bin/env python3
"""Bounded DNS, certificate, proxy, and security-header assurance probe."""
from __future__ import annotations

import argparse
import json
import socket
import ssl
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

USER_AGENT = "ClearGlass-Edge-Assurance/1 (+bounded-monitor)"


def validate_target(value: str) -> urllib.parse.SplitResult:
    if len(value) > 2048:
        raise ValueError("target URL is too long")
    parsed = urllib.parse.urlsplit(value)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise ValueError("target must be HTTPS without credentials, query, or fragment")
    return parsed


def resolve_addresses(hostname: str, port: int) -> list[str]:
    addresses = {
        item[4][0]
        for item in socket.getaddrinfo(hostname, port, type=socket.SOCK_STREAM)
        if item[0] in {socket.AF_INET, socket.AF_INET6}
    }
    return sorted(addresses)


def certificate(hostname: str, port: int) -> dict[str, Any]:
    context = ssl.create_default_context()
    with socket.create_connection((hostname, port), timeout=10) as raw:
        with context.wrap_socket(raw, server_hostname=hostname) as tls:
            cert = tls.getpeercert()
            expires = datetime.fromtimestamp(
                ssl.cert_time_to_seconds(cert["notAfter"]), timezone.utc
            )
            issuer = ",".join(
                f"{key}={value}" for component in cert.get("issuer", ()) for key, value in component
            )
            return {
                "expires_at": expires.isoformat().replace("+00:00", "Z"),
                "days_remaining": round(
                    (expires - datetime.now(timezone.utc)).total_seconds() / 86400, 2
                ),
                "issuer": issuer,
                "tls_version": tls.version(),
                "cipher": tls.cipher()[0] if tls.cipher() else None,
            }


def fetch(url: str) -> tuple[int, dict[str, str], str]:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            response.read(1024)
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.geturl()
    except urllib.error.HTTPError as exc:
        exc.read(1024)
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.geturl()


def assess_headers(
    headers: dict[str, str], *, require_cloudflare: bool, csp_mode: str
) -> tuple[list[str], list[str]]:
    failures: list[str] = []
    warnings: list[str] = []
    exact = {
        "x-content-type-options": "nosniff",
        "referrer-policy": "strict-origin-when-cross-origin",
    }
    required = ["strict-transport-security", "permissions-policy"]
    for name, value in exact.items():
        if headers.get(name, "").lower() != value:
            failures.append(f"{name} is missing or unexpected")
    for name in required:
        if not headers.get(name):
            failures.append(f"{name} is missing")
    if require_cloudflare and not headers.get("cf-ray"):
        failures.append("cf-ray is missing; target is not proven to traverse Cloudflare")
    if not require_cloudflare and not headers.get("cf-ray"):
        warnings.append("cf-ray is absent")
    report_only = bool(headers.get("content-security-policy-report-only"))
    enforcing = bool(headers.get("content-security-policy"))
    if csp_mode == "report-only" and (not report_only or enforcing):
        failures.append("CSP is not exclusively in report-only mode")
    if csp_mode == "enforce" and not enforcing:
        failures.append("enforcing Content-Security-Policy is missing")
    return failures, warnings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--expected-hostname", default="")
    parser.add_argument("--require-cloudflare", action="store_true")
    parser.add_argument("--csp-mode", choices=["none", "report-only", "enforce"], default="none")
    parser.add_argument("--minimum-certificate-days", type=int, default=21)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    failures: list[str] = []
    warnings: list[str] = []
    try:
        parsed = validate_target(args.base_url)
        if args.expected_hostname and parsed.hostname != args.expected_hostname.lower():
            raise ValueError("target hostname does not match the approved hostname")
        port = parsed.port or 443
        addresses = resolve_addresses(parsed.hostname, port)
        if not addresses:
            failures.append("DNS returned no A/AAAA addresses")
        cert = certificate(parsed.hostname, port)
        if cert["days_remaining"] < args.minimum_certificate_days:
            failures.append(
                f"certificate has only {cert['days_remaining']} days remaining "
                f"(< {args.minimum_certificate_days})"
            )
        status_code, headers, final_url = fetch(args.base_url)
        final = validate_target(final_url)
        if final.hostname != parsed.hostname:
            failures.append(f"request redirected to a different hostname: {final.hostname}")
        if not 200 <= status_code < 400:
            failures.append(f"HTTP status is {status_code}")
        header_failures, header_warnings = assess_headers(
            headers,
            require_cloudflare=args.require_cloudflare,
            csp_mode=args.csp_mode,
        )
        failures.extend(header_failures)
        warnings.extend(header_warnings)
        result = {
            "schema_version": 1,
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "hostname": parsed.hostname,
            "resolved_addresses": addresses,
            "certificate": cert,
            "http_status": status_code,
            "final_url": final_url,
            "cloudflare_ray_present": bool(headers.get("cf-ray")),
            "cf_cache_status": headers.get("cf-cache-status"),
            "csp_report_only_present": bool(headers.get("content-security-policy-report-only")),
            "csp_enforcing_present": bool(headers.get("content-security-policy")),
            "failures": failures,
            "warnings": warnings,
        }
    except (ValueError, OSError, ssl.SSLError, urllib.error.URLError) as exc:
        failures.append(f"probe failed: {type(exc).__name__}: {exc}")
        result = {
            "schema_version": 1,
            "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "hostname": urllib.parse.urlsplit(args.base_url).hostname,
            "failures": failures,
            "warnings": warnings,
        }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    for warning in warnings:
        print(f"WARN: {warning}")
    for failure in failures:
        print(f"ERROR: {failure}", file=sys.stderr)
    if failures:
        return 1
    print(f"Edge assurance passed for {result['hostname']}; certificate days={result['certificate']['days_remaining']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
