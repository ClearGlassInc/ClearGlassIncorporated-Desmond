#!/usr/bin/env python3
"""Fail closed on unsafe edge-IaC and workflow changes.

This is intentionally a small, dependency-free static guard. Terraform validate
remains authoritative for provider syntax; these checks protect repository-level
invariants that Terraform cannot express, such as not managing DNS here.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_ROOT = ROOT.parents[1]
WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "edge-security.yml"
STATE_IMPORT_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "edge-state-import.yml"
ASSURANCE_WORKFLOW = REPOSITORY_ROOT / ".github" / "workflows" / "edge-assurance.yml"
ENVIRONMENTS = ROOT / "environments"
LEGACY_EDGE = REPOSITORY_ROOT / "clearglass-commerce" / "infra" / "cloudflare"


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


FEATURE_FLAGS = {
    "enable_custom_waf",
    "enable_managed_waf",
    "enable_bot_management",
    "enable_bot_score_rule",
    "enable_provider_reputation_rules",
    "enable_rate_limits",
    "enable_security_headers",
    "enable_logpush",
    "enable_geo_asn_rules",
    "enable_origin_auth_header",
    "enable_enterprise_body_size_rule",
    "enable_emergency_mode",
}
STAGE_RANK = {"disabled": 0, "observe": 1, "challenge": 2, "enforce": 3}
CUSTOM_ACTION_KEYS = {"unexpected_method", "path_probe", "suspicious_ua", "request_size", "request_body"}
RATE_ACTION_KEYS = {"static_assets", "html", "login", "password_reset", "search", "contact_form", "api", "admin", "webhook"}


def actions(config: dict[str, object], name: str) -> list[str]:
    value = config.get(name, {})
    return list(value.values()) if isinstance(value, dict) else []


def rfc3339(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def validate_environment(path: Path, policy_version: str, errors: list[str]) -> dict[str, object] | None:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"{path}: invalid environment JSON: {exc}")
        return None
    require(isinstance(config, dict), f"{path}: top level must be an object", errors)
    if not isinstance(config, dict):
        return None

    for key in FEATURE_FLAGS:
        require(isinstance(config.get(key), bool), f"{path}: {key} must be an explicit boolean", errors)

    stage = config.get("rollout_stage")
    require(stage in STAGE_RANK, f"{path}: rollout_stage must be disabled/observe/challenge/enforce", errors)
    require(config.get("policy_version") == policy_version, f"{path}: policy_version must match neutral policy {policy_version}", errors)
    require(config.get("csp_mode") in {"report-only", "enforce"}, f"{path}: csp_mode must be report-only or enforce", errors)
    mutation_enabled = any(config.get(key) is True for key in FEATURE_FLAGS)
    require(
        (stage == "disabled") == (not mutation_enabled),
        f"{path}: rollout_stage must be disabled exactly when all provider features are false",
        errors,
    )

    if mutation_enabled:
        require(bool(str(config.get("deployment_owner", "")).strip()), f"{path}: enabled config requires deployment_owner", errors)
        require(bool(str(config.get("deployment_change_ticket", "")).strip()), f"{path}: enabled config requires deployment_change_ticket", errors)
        require(
            len(str(config.get("configuration_rationale", "")).strip()) >= 10,
            f"{path}: enabled config requires a meaningful configuration_rationale",
            errors,
        )

    custom_map = config.get("custom_waf_actions")
    rate_map = config.get("rate_limit_actions")
    custom_actions = actions(config, "custom_waf_actions")
    rate_actions = actions(config, "rate_limit_actions")
    require(isinstance(custom_map, dict), f"{path}: custom_waf_actions must be an object", errors)
    require(isinstance(rate_map, dict), f"{path}: rate_limit_actions must be an object", errors)
    require(set(custom_map or {}) == CUSTOM_ACTION_KEYS, f"{path}: custom_waf_actions must define every known custom rule exactly once", errors)
    require(set(rate_map or {}) == RATE_ACTION_KEYS, f"{path}: rate_limit_actions must define every route class exactly once", errors)
    require(all(action in {"log", "managed_challenge", "block"} for action in custom_actions), f"{path}: custom_waf_actions contains an unsupported action", errors)
    require(all(action in {"log", "managed_challenge", "block"} for action in rate_actions), f"{path}: rate_limit_actions contains an unsupported action", errors)
    require(not isinstance(rate_map, dict) or rate_map.get("webhook") != "managed_challenge", f"{path}: webhook rate limit cannot use a browser managed challenge", errors)
    if stage == "disabled":
        require(all(action == "log" for action in custom_actions), f"{path}: disabled baseline custom WAF actions must be log", errors)
        require(all(action == "log" for action in rate_actions), f"{path}: disabled baseline rate actions must be log", errors)
        require(config.get("managed_waf_override_action") == "log", f"{path}: disabled baseline managed WAF action must be log", errors)
        require(config.get("bot_score_action") == "log", f"{path}: disabled baseline bot-score action must be log", errors)
        require(config.get("provider_reputation_action") == "log", f"{path}: disabled baseline reputation action must be log", errors)
        require(config.get("csp_mode") == "report-only", f"{path}: disabled baseline CSP must be report-only", errors)

    if stage == "observe":
        require(not config.get("enable_custom_waf") or all(action == "log" for action in custom_actions), f"{path}: observe custom WAF must be log-only", errors)
        require(not config.get("enable_rate_limits") or all(action == "log" for action in rate_actions), f"{path}: observe rate limits must be log-only", errors)
        require(not config.get("enable_managed_waf") or config.get("managed_waf_override_action") == "log", f"{path}: observe managed WAF must be log-only", errors)
        require(not config.get("enable_bot_score_rule") or config.get("bot_score_action") == "log", f"{path}: observe bot score must be log-only", errors)
        require(not config.get("enable_provider_reputation_rules") or config.get("provider_reputation_action") == "log", f"{path}: observe reputation must be log-only", errors)
        for feature in ("enable_bot_management", "enable_geo_asn_rules", "enable_emergency_mode"):
            require(not config.get(feature), f"{path}: {feature} cannot run in observe stage", errors)
        require(config.get("csp_mode") == "report-only", f"{path}: observe CSP must be report-only", errors)

    if stage in {"challenge", "enforce"}:
        evidence = config.get("promotion_evidence_sha256")
        start = rfc3339(config.get("observation_window_start"))
        end = rfc3339(config.get("observation_window_end"))
        require(
            isinstance(evidence, str) and re.fullmatch(r"[0-9a-f]{64}", evidence) is not None,
            f"{path}: challenge/enforce promotion requires promotion_evidence_sha256",
            errors,
        )
        require(start is not None and end is not None, f"{path}: promotion observation timestamps must be RFC3339", errors)
        if start is not None and end is not None:
            require(end - start >= timedelta(days=7), f"{path}: promotion observation window must span at least seven days", errors)
            require(end <= datetime.now(timezone.utc), f"{path}: promotion observation window cannot end in the future", errors)

    terminal = (
        (config.get("enable_custom_waf") and "block" in custom_actions)
        or (config.get("enable_managed_waf") and config.get("managed_waf_override_action") == "block")
        or (config.get("enable_rate_limits") and "block" in rate_actions)
        or (config.get("enable_bot_score_rule") and config.get("bot_score_action") == "block")
        or (
            config.get("enable_bot_management")
            and "block" in {
                config.get("bot_definitely_automated_action"),
                config.get("bot_likely_automated_action"),
            }
        )
    )
    require(not terminal or stage == "enforce", f"{path}: active block actions require rollout_stage=enforce", errors)

    challenge = (
        (config.get("enable_custom_waf") and "managed_challenge" in custom_actions)
        or (config.get("enable_managed_waf") and config.get("managed_waf_override_action") == "managed_challenge")
        or (config.get("enable_rate_limits") and "managed_challenge" in rate_actions)
        or (config.get("enable_bot_score_rule") and config.get("bot_score_action") == "managed_challenge")
        or config.get("enable_bot_management")
        or config.get("enable_geo_asn_rules")
        or config.get("enable_emergency_mode")
    )
    require(
        not challenge or stage in {"challenge", "enforce"},
        f"{path}: active challenge controls require rollout_stage=challenge or enforce",
        errors,
    )

    high_impact = (
        config.get("enable_origin_auth_header")
        or (config.get("enable_security_headers") and config.get("csp_mode") == "enforce")
        or config.get("log_full_client_ip")
        or config.get("hsts_include_subdomains")
        or config.get("hsts_preload")
    )
    require(not high_impact or stage == "enforce", f"{path}: origin auth, full IP logging, and expanded HSTS require enforce stage", errors)

    for dependent in (
        "enable_bot_score_rule",
        "enable_provider_reputation_rules",
        "enable_geo_asn_rules",
        "enable_enterprise_body_size_rule",
        "enable_emergency_mode",
    ):
        require(
            not config.get(dependent) or config.get("enable_custom_waf") is True,
            f"{path}: {dependent} requires enable_custom_waf=true",
            errors,
        )
    require(config.get("log_full_client_ip") is False or config.get("enable_logpush") is True, f"{path}: full client IP has no purpose unless Logpush is enabled", errors)
    return config


def main() -> int:
    errors: list[str] = []
    terraform_files = sorted(ROOT.glob("*.tf"))
    terraform = "\n".join(path.read_text(encoding="utf-8") for path in terraform_files)
    workflow = WORKFLOW.read_text(encoding="utf-8")
    state_import_workflow = STATE_IMPORT_WORKFLOW.read_text(encoding="utf-8")
    assurance_workflow = ASSURANCE_WORKFLOW.read_text(encoding="utf-8")
    legacy_guard = (LEGACY_EDGE / "ownership_guard.tf").read_text(encoding="utf-8")

    require('version = "= 4.40.0"' in terraform, "Cloudflare provider must remain exactly pinned", errors)
    require('required_version = ">= 1.10.0, < 2.0.0"' in terraform, "Terraform version must support native S3 lock files", errors)
    require('backend "s3"' in terraform, "locked remote-state backend declaration is required", errors)
    require('resource "cloudflare_record"' not in terraform, "edge module must not manage DNS records", errors)
    require('resource "cloudflare_dns_record"' not in terraform, "edge module must not manage DNS records", errors)
    require("terraform destroy" not in workflow.lower(), "workflow must not expose Terraform destroy", errors)
    require("cloudflare_record" not in workflow, "workflow must not make DNS changes", errors)
    require("terraform apply" not in state_import_workflow, "state-import workflow must never apply provider changes", errors)
    require("terraform destroy" not in state_import_workflow, "state-import workflow must never destroy resources", errors)
    require("cloudflare_record" not in state_import_workflow, "state-import workflow must not make DNS changes", errors)
    for token, label in {
        'name: edge-${{ inputs.environment }}': "protected write environment",
        "EDGE_TF_IMPORT_MANIFEST_B64": "sealed import manifest",
        "EXPECTED_MANIFEST_SHA256": "reviewed manifest digest",
        "infra/edge/scripts/import_state.py": "allowlisted import validator",
        "Provider apply was not attempted": "no-apply audit statement",
    }.items():
        require(token in state_import_workflow, f"state-import workflow is missing {label}", errors)
    require("terraform apply" not in assurance_workflow, "assurance workflow must never apply provider changes", errors)
    require("terraform destroy" not in assurance_workflow, "assurance workflow must never destroy resources", errors)
    require("--execute" not in assurance_workflow, "scheduled assurance must not execute negative probes", errors)
    for token, label in {
        "schedule:": "periodic schedule",
        "EDGE_ASSURANCE_ENABLED": "explicit schedule enable gate",
        "EDGE_DRIFT_ENABLED": "explicit drift enable gate",
        "assurance_check.py": "DNS/TLS/certificate assurance",
        "-detailed-exitcode": "drift-sensitive Terraform plan",
        'name: edge-${{ inputs.environment || \'staging\' }}-plan': "protected read environment",
        "negative_security_test.py --base-url \"$BASE_URL\" --dry-run": "bounded dry-run negative check",
    }.items():
        require(token in assurance_workflow, f"assurance workflow is missing {label}", errors)
    require(
        'variable "allow_legacy_edge_stack_mutation"' in legacy_guard
        and "default     = false" in legacy_guard
        and "precondition" in legacy_guard,
        "legacy Cloudflare stack must remain frozen behind a default-deny precondition",
        errors,
    )

    phase_expectations = {
        "http_request_firewall_custom": 1,
        "http_request_firewall_managed": 1,
        "http_ratelimit": 1,
        "http_response_headers_transform": 1,
        "http_request_late_transform": 1,
    }
    for phase, expected in phase_expectations.items():
        actual = len(re.findall(rf'phase\s*=\s*"{re.escape(phase)}"', terraform))
        require(actual == expected, f"expected exactly {expected} owner for Cloudflare phase {phase}; found {actual}", errors)

    waf = (ROOT / "waf.tf").read_text(encoding="utf-8")
    rates = (ROOT / "rate_limits.tf").read_text(encoding="utf-8")
    origin = (ROOT / "origin.tf").read_text(encoding="utf-8")
    require(
        waf.count("expression  = local.protected_host_scope") >= 2,
        "both managed WAF entry points must cover public, API, and admin hostnames",
        errors,
    )
    require('ref         = "rl_webhook"' in rates, "webhook-specific rate limit is required", errors)
    require(
        'lookup(var.rate_limit_actions, "webhook", "log")' in rates,
        "webhook rate-limit default must remain non-interactive log mode",
        errors,
    )
    require(
        "local.dynamic_host_scope" in origin and "local.host_scope" not in origin,
        "origin authentication must apply only to dynamic origins, never GitHub Pages",
        errors,
    )

    workflow_invariants = {
        "protected remote-state configuration": "EDGE_TF_BACKEND_CONFIG_B64",
        "separate plan credential": "CLOUDFLARE_EDGE_PLAN_TOKEN",
        "separate apply credential": "CLOUDFLARE_EDGE_APPLY_TOKEN",
        "state lock": "use_lockfile",
        "pinned Terraform binary digest": "TF_LINUX_AMD64_SHA256",
        "reviewed plan digest": "EXPECTED_PLAN_SHA",
        "production approval environment": 'name: edge-${{ inputs.environment }}',
        "rollback ancestry guard": "git merge-base --is-ancestor",
        "emergency expiry": "EMERGENCY_EXPIRES_AT",
        "protected CSP report URI": "EDGE_CSP_REPORT_URI",
    }
    for label, token in workflow_invariants.items():
        require(token in workflow, f"workflow is missing {label}", errors)
    require("custom_waf_action:" not in workflow, "workflow must not accept an unreviewed global WAF-action input", errors)
    require("rate_limit_action:" not in workflow, "workflow must not accept an unreviewed global rate-action input", errors)

    try:
        neutral_policy = json.loads((ROOT / "policies" / "baseline.json").read_text(encoding="utf-8"))
        policy_version = neutral_policy["version"]
    except (OSError, json.JSONDecodeError, KeyError) as exc:
        errors.append(f"cannot read neutral policy version: {exc}")
        policy_version = "INVALID"

    configs = {
        name: validate_environment(ENVIRONMENTS / f"{name}.tfvars.json", policy_version, errors)
        for name in ("staging", "production")
    }
    staging = configs["staging"]
    production = configs["production"]
    if staging and production:
        staging_stage = str(staging.get("rollout_stage"))
        production_stage = str(production.get("rollout_stage"))
        if staging_stage in STAGE_RANK and production_stage in STAGE_RANK:
            require(
                STAGE_RANK[production_stage] <= STAGE_RANK[staging_stage],
                "production rollout_stage cannot be ahead of staging",
                errors,
            )
        for feature in sorted(FEATURE_FLAGS - {"enable_emergency_mode"}):
            require(
                production.get(feature) is not True or staging.get(feature) is True,
                f"production {feature}=true requires the same staging feature to be enabled",
                errors,
            )
    declared_variables = set(re.findall(r'^variable\s+"([A-Za-z0-9_]+)"', terraform, flags=re.MULTILINE))
    for name, config in configs.items():
        if config:
            unknown = set(config) - declared_variables
            require(not unknown, f"{name} environment contains undeclared Terraform variables: {sorted(unknown)}", errors)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(f"Terraform safety validation failed with {len(errors)} error(s).", file=sys.stderr)
        return 1
    print(f"Terraform safety OK: {len(terraform_files)} files, locked state, no DNS resources, staged environments")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
