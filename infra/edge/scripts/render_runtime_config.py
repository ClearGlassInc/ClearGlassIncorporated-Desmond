#!/usr/bin/env python3
"""Render ephemeral Terraform runtime inputs from protected CI variables."""

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable


def json_list(name: str, validator: Callable[[Any], bool] | None = None) -> list[Any]:
    raw = os.getenv(name, "").strip() or "[]"
    try:
        value = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} must contain valid JSON: {exc.msg}") from exc
    if not isinstance(value, list):
        raise ValueError(f"{name} must contain a JSON array")
    if validator and not all(validator(item) for item in value):
        raise ValueError(f"{name} contains an invalid value")
    return value


def is_cidr(value: Any, version: int) -> bool:
    try:
        return ipaddress.ip_network(str(value), strict=False).version == version
    except ValueError:
        return False


def is_asn(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and 1 <= value <= 4_294_967_295


def is_country(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[A-Za-z]{2}", value) is not None


def hostname(name: str, default: str = "", required: bool = False) -> str:
    value = os.getenv(name, "").strip() or default
    if required and not value:
        raise ValueError(f"{name} is required")
    if value and re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?", value) is None:
        raise ValueError(f"{name} must be a hostname without a scheme or path")
    return value.lower()


def parse_time(value: str) -> datetime:
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        raise ValueError("timestamp must include a timezone")
    return parsed.astimezone(timezone.utc)


def load_policy_inputs(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load committed environment configuration {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError("committed environment configuration must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--policy-inputs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--emergency", action="store_true")
    parser.add_argument("--emergency-expires-at", default="")
    parser.add_argument("--emergency-owner", default="")
    parser.add_argument("--change-ticket", default="")
    args = parser.parse_args()

    try:
        policy_inputs = load_policy_inputs(args.policy_inputs)
        account_id = os.getenv("EDGE_CLOUDFLARE_ACCOUNT_ID", "").strip()
        zone_id = os.getenv("EDGE_CLOUDFLARE_ZONE_ID", "").strip()
        if re.fullmatch(r"[0-9a-fA-F]{32}", account_id) is None or re.fullmatch(r"[0-9a-fA-F]{32}", zone_id) is None:
            raise ValueError("EDGE_CLOUDFLARE_ACCOUNT_ID and EDGE_CLOUDFLARE_ZONE_ID must be 32-character hexadecimal identifiers")

        data: dict[str, Any] = {
            "account_id": account_id,
            "zone_id": zone_id,
            "zone_name": hostname("EDGE_ZONE_NAME", "clearglassinc.com", required=True),
            "public_hostname": hostname("EDGE_PUBLIC_HOSTNAME", "www.clearglassinc.com", required=True),
            "api_hostname": hostname("EDGE_API_HOSTNAME"),
            "admin_hostname": hostname("EDGE_ADMIN_HOSTNAME"),
            "trusted_ipv4_cidrs": json_list("EDGE_TRUSTED_IPV4_CIDRS_JSON", lambda item: is_cidr(item, 4)),
            "trusted_ipv6_cidrs": json_list("EDGE_TRUSTED_IPV6_CIDRS_JSON", lambda item: is_cidr(item, 6)),
            "monitoring_ipv4_cidrs": json_list("EDGE_MONITORING_IPV4_CIDRS_JSON", lambda item: is_cidr(item, 4)),
            "monitoring_ipv6_cidrs": json_list("EDGE_MONITORING_IPV6_CIDRS_JSON", lambda item: is_cidr(item, 6)),
            "internal_automation_ipv4_cidrs": json_list("EDGE_AUTOMATION_IPV4_CIDRS_JSON", lambda item: is_cidr(item, 4)),
            "internal_automation_ipv6_cidrs": json_list("EDGE_AUTOMATION_IPV6_CIDRS_JSON", lambda item: is_cidr(item, 6)),
            "deny_ipv4_cidrs": json_list("EDGE_DENY_IPV4_CIDRS_JSON", lambda item: is_cidr(item, 4)),
            "deny_ipv6_cidrs": json_list("EDGE_DENY_IPV6_CIDRS_JSON", lambda item: is_cidr(item, 6)),
            "quarantine_ipv4_cidrs": json_list("EDGE_QUARANTINE_IPV4_CIDRS_JSON", lambda item: is_cidr(item, 4)),
            "quarantine_ipv6_cidrs": json_list("EDGE_QUARANTINE_IPV6_CIDRS_JSON", lambda item: is_cidr(item, 6)),
            "quarantine_expires_at": os.getenv("EDGE_QUARANTINE_EXPIRES_AT", "").strip(),
            "trusted_asns": json_list("EDGE_TRUSTED_ASNS_JSON", is_asn),
            "denied_asns": json_list("EDGE_DENIED_ASNS_JSON", is_asn),
            "challenge_asns": json_list("EDGE_CHALLENGE_ASNS_JSON", is_asn),
            "allowed_countries": json_list("EDGE_ALLOWED_COUNTRIES_JSON", is_country),
            "denied_countries": json_list("EDGE_DENIED_COUNTRIES_JSON", is_country),
            "challenge_countries": json_list("EDGE_CHALLENGE_COUNTRIES_JSON", is_country),
            "geo_exception_countries": json_list("EDGE_GEO_EXCEPTION_COUNTRIES_JSON", is_country),
            "anonymous_network_ip_list_name": os.getenv("EDGE_ANONYMOUS_NETWORK_IP_LIST_NAME", "").strip(),
            "tor_exit_ip_list_name": os.getenv("EDGE_TOR_EXIT_IP_LIST_NAME", "").strip(),
            "logpush_destination": os.getenv("EDGE_LOGPUSH_DESTINATION", ""),
            "origin_auth_header_name": os.getenv("EDGE_ORIGIN_AUTH_HEADER_NAME", "").strip() or "X-ClearGlass-Edge-Origin",
            "origin_auth_header_value": os.getenv("EDGE_ORIGIN_AUTH_HEADER_VALUE", ""),
            "csp_report_uri": os.getenv("EDGE_CSP_REPORT_URI", "").strip(),
        }

        zone_name = data["zone_name"]
        for field in ("public_hostname", "api_hostname", "admin_hostname"):
            value = data[field]
            if value and value != zone_name and not value.endswith("." + zone_name):
                raise ValueError(f"{field} must belong to EDGE_ZONE_NAME")
        protected_hosts = [data[field] for field in ("public_hostname", "api_hostname", "admin_hostname") if data[field]]
        if len(protected_hosts) != len(set(protected_hosts)):
            raise ValueError("public, API, and admin hostnames must be distinct")

        quarantine = data["quarantine_ipv4_cidrs"] + data["quarantine_ipv6_cidrs"]
        if quarantine:
            expiry = parse_time(data["quarantine_expires_at"])
            if expiry <= datetime.now(timezone.utc):
                raise ValueError("EDGE_QUARANTINE_EXPIRES_AT must be in the future when quarantine lists are populated")

        if policy_inputs.get("enable_logpush") and not data["logpush_destination"]:
            raise ValueError("enable_logpush=true requires EDGE_LOGPUSH_DESTINATION")
        if policy_inputs.get("enable_origin_auth_header"):
            if not data["api_hostname"] and not data["admin_hostname"]:
                raise ValueError("enable_origin_auth_header=true requires EDGE_API_HOSTNAME or EDGE_ADMIN_HOSTNAME")
            if len(data["origin_auth_header_value"]) < 32:
                raise ValueError("enable_origin_auth_header=true requires a 32+ character EDGE_ORIGIN_AUTH_HEADER_VALUE")

        if data["csp_report_uri"]:
            report_uri = urllib.parse.urlsplit(data["csp_report_uri"])
            if (
                report_uri.scheme != "https"
                or report_uri.hostname != data["api_hostname"]
                or report_uri.path != "/api/security/csp-report"
                or report_uri.query
                or report_uri.fragment
                or report_uri.username
                or report_uri.password
            ):
                raise ValueError(
                    "EDGE_CSP_REPORT_URI must be the HTTPS /api/security/csp-report endpoint "
                    "on EDGE_API_HOSTNAME without credentials, query, or fragment"
                )
        if policy_inputs.get("csp_mode") == "enforce" and not data["csp_report_uri"]:
            raise ValueError("csp_mode=enforce requires EDGE_CSP_REPORT_URI")

        if args.emergency:
            if not policy_inputs.get("enable_custom_waf"):
                raise ValueError("emergency mode requires enable_custom_waf=true in the reviewed environment configuration")
            if not args.emergency_owner.strip() or not args.change_ticket.strip():
                raise ValueError("emergency mode requires an operator and change ticket")
            expiry = parse_time(args.emergency_expires_at)
            now = datetime.now(timezone.utc)
            if not now < expiry <= now + timedelta(hours=24):
                raise ValueError("emergency expiry must be in the future and no more than 24 hours away")
            data.update(
                {
                    "enable_emergency_mode": True,
                    "emergency_expires_at": args.emergency_expires_at,
                    "emergency_owner": args.emergency_owner.strip(),
                    "emergency_change_ticket": args.change_ticket.strip(),
                }
            )

        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        args.output.chmod(0o600)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Runtime edge configuration prepared at {args.output}; values were not printed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
