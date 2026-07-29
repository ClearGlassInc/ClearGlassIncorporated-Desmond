#!/usr/bin/env python3
"""Fail-closed validation for the auto-store production deployment boundary."""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from urllib.parse import urlsplit


CHANGE_TICKET_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{1,31}-[1-9][0-9]{0,11}")
REQUIRED_URLS = ("RENDER_DEPLOY_HOOK_URL", "RENDER_ROLLBACK_HOOK_URL", "CONTROL_PLANE_URL")


def validate_configuration(environment: Mapping[str, str]) -> list[str]:
    """Return safe, actionable errors without ever returning secret values."""
    errors: list[str] = []
    ticket = environment.get("CHANGE_TICKET", "").strip()
    if not ticket:
        errors.append("change_ticket input is required")
    elif not CHANGE_TICKET_PATTERN.fullmatch(ticket):
        errors.append("change_ticket must be a bounded reference such as CHG-1234")

    parsed_urls = {}
    for name in REQUIRED_URLS:
        value = environment.get(name, "").strip()
        if not value:
            errors.append(f"{name} is required")
            continue
        parsed = urlsplit(value)
        parsed_urls[name] = parsed
        if parsed.scheme != "https" or not parsed.hostname:
            errors.append(f"{name} must be an absolute HTTPS URL")
        if parsed.username or parsed.password:
            errors.append(f"{name} must not contain URL credentials")
        if parsed.fragment:
            errors.append(f"{name} must not contain a fragment")

    control_plane = parsed_urls.get("CONTROL_PLANE_URL")
    if control_plane and control_plane.query:
        errors.append("CONTROL_PLANE_URL must not contain a query string")

    deploy_hook = environment.get("RENDER_DEPLOY_HOOK_URL", "").strip()
    rollback_hook = environment.get("RENDER_ROLLBACK_HOOK_URL", "").strip()
    if deploy_hook and deploy_hook == rollback_hook:
        errors.append("deploy and rollback hooks must be different")

    return errors


def main() -> int:
    errors = validate_configuration(os.environ)
    if not errors:
        print("Production deployment configuration is valid.")
        return 0

    print("::error::Production deployment is not authorized/configured.")
    for error in errors:
        print(f"::error::{error}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("### Production deployment blocked\n")
            handle.writelines(f"- {error}\n" for error in errors)
            handle.write("- No release marker was promoted and no deployment was attempted.\n")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
