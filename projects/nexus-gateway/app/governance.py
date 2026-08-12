import json
from dataclasses import dataclass
from typing import Any

from .config import Settings
from .models import AIActionRequest


@dataclass(frozen=True)
class GovernanceDecision:
    allowed: bool
    reason: str


FORBIDDEN_CONTROL_KEYS = {
    "system_prompt",
    "developer_prompt",
    "override_policy",
    "disable_guardrails",
    "bypass_authorization",
    "raw_shell",
    "shell_command",
}


TOOL_SCHEMAS: dict[str, set[str]] = {
    "network_optimizer": {"mode", "adapter", "diagnostic_only", "duration_seconds"},
    "telemetry_parser": {"format", "source", "records"},
    "aegis_scan": {"mode", "scan_minutes", "generate_report"},
}


def evaluate_action(action: AIActionRequest, settings: Settings) -> GovernanceDecision:
    if action.target_tool not in settings.tool_allowlist:
        return GovernanceDecision(False, f"Tool '{action.target_tool}' is outside the configured capability allowlist.")

    encoded = json.dumps(action.payload, separators=(",", ":"), sort_keys=True, default=str).encode("utf-8")
    if len(encoded) > settings.max_payload_bytes:
        return GovernanceDecision(False, "Payload exceeds the configured governance size limit.")

    lowered_keys = {str(key).lower() for key in action.payload.keys()}
    forbidden = lowered_keys.intersection(FORBIDDEN_CONTROL_KEYS)
    if forbidden:
        return GovernanceDecision(False, f"Payload contains forbidden control fields: {', '.join(sorted(forbidden))}.")

    schema = TOOL_SCHEMAS.get(action.target_tool)
    if schema is not None:
        unexpected = lowered_keys.difference(schema)
        if unexpected:
            return GovernanceDecision(False, f"Payload contains fields not authorized for this tool: {', '.join(sorted(unexpected))}.")

    if action.target_tool == "network_optimizer" and action.payload.get("diagnostic_only") is False:
        return GovernanceDecision(False, "Remote mutating network optimization is disabled at the gateway boundary.")

    return GovernanceDecision(True, "Action satisfies capability, objective-binding, and payload policy checks.")
