#!/usr/bin/env python3
"""Validate and optionally execute an allowlisted single-owner state import."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ImportSpec:
    feature_flag: str
    identifier: re.Pattern[str]


ZONE = r"[0-9a-f]{32}"
RULESET = re.compile(rf"^zone/({ZONE})/({ZONE})$")
LOGPUSH = re.compile(rf"^zone/({ZONE})/([1-9][0-9]*)$")
BOT = re.compile(rf"^({ZONE})$")

ALLOWED_IMPORTS = {
    "cloudflare_ruleset.custom_waf[0]": ImportSpec("enable_custom_waf", RULESET),
    "cloudflare_ruleset.managed_waf[0]": ImportSpec("enable_managed_waf", RULESET),
    "cloudflare_ruleset.rate_limits[0]": ImportSpec("enable_rate_limits", RULESET),
    "cloudflare_ruleset.security_headers[0]": ImportSpec("enable_security_headers", RULESET),
    "cloudflare_ruleset.dynamic_origin_auth[0]": ImportSpec("enable_origin_auth_header", RULESET),
    "cloudflare_bot_management.public_perimeter[0]": ImportSpec("enable_bot_management", BOT),
    "cloudflare_logpush_job.firewall_events[0]": ImportSpec("enable_logpush", LOGPUSH),
}
CHANGE_TICKET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{1,127}$")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")


def timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load {label} {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def validate_manifest(
    manifest: dict[str, Any], policy: dict[str, Any], expected_zone_id: str
) -> list[tuple[str, str]]:
    errors: list[str] = []
    if manifest.get("schema_version") != 1:
        errors.append("schema_version must be 1")
    environment = manifest.get("environment")
    if environment not in {"staging", "production"}:
        errors.append("environment must be staging or production")
    zone_id = manifest.get("zone_id")
    if zone_id != expected_zone_id or re.fullmatch(ZONE, str(zone_id)) is None:
        errors.append("zone_id must exactly match the protected runtime zone")
    ticket = manifest.get("change_ticket")
    if not isinstance(ticket, str) or CHANGE_TICKET.fullmatch(ticket) is None:
        errors.append("change_ticket is invalid")
    if ticket != policy.get("deployment_change_ticket"):
        errors.append("manifest change_ticket must match the reviewed environment configuration")
    captured = timestamp(manifest.get("captured_at"))
    if captured is None or captured > datetime.now(timezone.utc):
        errors.append("captured_at must be a completed RFC3339 timestamp")

    legacy = manifest.get("legacy_state")
    if not isinstance(legacy, dict):
        errors.append("legacy_state must be an object")
    else:
        if legacy.get("stack_path") != "clearglass-commerce/infra/cloudflare":
            errors.append("legacy_state.stack_path must name the frozen legacy stack")
        if not isinstance(legacy.get("serial"), int) or legacy.get("serial", -1) < 0:
            errors.append("legacy_state.serial must be a non-negative state serial")
        if not isinstance(legacy.get("snapshot_sha256"), str) or SHA256.fullmatch(
            legacy.get("snapshot_sha256", "")
        ) is None:
            errors.append("legacy_state.snapshot_sha256 must be a lowercase SHA-256")
        if legacy.get("resources_detached") is not True:
            errors.append("legacy_state.resources_detached must explicitly be true")
        if legacy.get("stack_frozen") is not True:
            errors.append("legacy_state.stack_frozen must explicitly be true")
        if not isinstance(legacy.get("frozen_commit"), str) or COMMIT.fullmatch(
            legacy.get("frozen_commit", "")
        ) is None:
            errors.append("legacy_state.frozen_commit must be a full commit SHA")

    imports = manifest.get("imports")
    validated: list[tuple[str, str]] = []
    if not isinstance(imports, list) or not imports:
        errors.append("imports must be a non-empty array")
    else:
        addresses: set[str] = set()
        identifiers: set[str] = set()
        for index, item in enumerate(imports):
            if not isinstance(item, dict) or set(item) != {"address", "id"}:
                errors.append(f"imports[{index}] must contain exactly address and id")
                continue
            address = item.get("address")
            identifier = item.get("id")
            if not isinstance(address, str) or address not in ALLOWED_IMPORTS:
                errors.append(f"imports[{index}].address is not allowlisted")
                continue
            spec = ALLOWED_IMPORTS[address]
            if not isinstance(identifier, str) or spec.identifier.fullmatch(identifier) is None:
                errors.append(f"imports[{index}].id has the wrong provider import format")
                continue
            import_zone = identifier.split("/")[1] if identifier.startswith("zone/") else identifier
            if import_zone != expected_zone_id:
                errors.append(f"imports[{index}].id belongs to a different zone")
            if policy.get(spec.feature_flag) is not True:
                errors.append(
                    f"{address} requires {spec.feature_flag}=true in the reviewed environment configuration"
                )
            if address in addresses:
                errors.append(f"duplicate import address: {address}")
            if identifier in identifiers:
                errors.append(f"duplicate provider import id: {identifier}")
            addresses.add(address)
            identifiers.add(identifier)
            validated.append((address, identifier))
    if errors:
        raise ValueError("\n".join(errors))
    return validated


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        check=True,
        text=True,
        capture_output=capture,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--policy-inputs", type=Path, required=True)
    parser.add_argument("--zone-id", required=True)
    parser.add_argument("--terraform-dir", type=Path, default=Path("infra/edge"))
    parser.add_argument("--runtime-inputs", type=Path)
    parser.add_argument("--terraform-bin", default="terraform")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--confirmation",
        default="",
        help="Execution only: exact '<environment>:<change_ticket>:IMPORT'.",
    )
    args = parser.parse_args()

    try:
        manifest = load_object(args.manifest, "import manifest")
        policy = load_object(args.policy_inputs, "policy inputs")
        imports = validate_manifest(manifest, policy, args.zone_id)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Validated {len(imports)} allowlisted import(s) for {manifest['environment']}.")
    if not args.execute:
        print("Validation only; remote state was not changed.")
        return 0

    expected_confirmation = f"{manifest['environment']}:{manifest['change_ticket']}:IMPORT"
    if args.confirmation != expected_confirmation:
        print(f"ERROR: execution requires confirmation {expected_confirmation!r}", file=sys.stderr)
        return 2
    if args.runtime_inputs is None:
        print("ERROR: --runtime-inputs is required for execution", file=sys.stderr)
        return 2

    tf = [args.terraform_bin, f"-chdir={args.terraform_dir}"]
    try:
        tracked_result = run(tf + ["state", "list"], capture=True)
        tracked = set(tracked_result.stdout.splitlines())
        conflicts = [address for address, _ in imports if address in tracked]
        if conflicts:
            raise RuntimeError(f"destination state already tracks: {', '.join(conflicts)}")
        for address, identifier in imports:
            print(f"Importing {address} with the locked remote backend.")
            run(
                tf
                + [
                    "import",
                    "-input=false",
                    "-lock-timeout=5m",
                    f"-var-file={args.policy_inputs.resolve()}",
                    f"-var-file={args.runtime_inputs.resolve()}",
                    address,
                    identifier,
                ]
            )
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"ERROR: state import stopped: {exc}", file=sys.stderr)
        print("Inspect `terraform state list` before retrying; earlier imports may have completed.", file=sys.stderr)
        return 1
    print("State import completed. Review a refresh-only plan and a normal plan; no provider apply was run.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
