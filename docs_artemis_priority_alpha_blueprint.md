# ClearGlassInc Artemis — Priority Sequence Alpha Implementation Packet

## System Architecture

Priority Sequence Alpha extends ClearGlassInc Artemis with an operator-command execution lane for time-sensitive intelligence work. The lane runs on Palantir Gotham for operational case context, Foundry for governed data products and Ontology actions, AIP for agent planning and human-in-the-loop copilots, and Apollo for controlled release, rollback, and runtime enforcement.

```text
Operator Console
  -> FastAPI Command Gateway
  -> Policy Decision Point
  -> AIP Orchestrator
  -> Foundry Ontology Actions
  -> Gotham Case/Entity Views
  -> Immutable Audit Ledger
  -> Apollo Release + Runtime Controls
```

The execution lane never assumes calendar, document, or signature authority. If a required object cannot be resolved by source system and event/document ID, Artemis blocks mutation, emits an audit event, and gives the operator a manual execution packet.

## Data and Ontology

Priority Sequence Alpha adds mission objects that make executive deconfliction and sign-off auditable:

| Object | Purpose | Critical fields |
| --- | --- | --- |
| `CommandPacket` | Ordered operator intent and constraints | `packet_id`, `priority_order`, `deadline`, `commander_id`, `status` |
| `CalendarConflict` | Conflict candidate with source trace | `event_ids`, `confidence`, `calendar_source`, `resolution_state` |
| `RiskSignoff` | Human-approved vendor or mission risk decision | `controls`, `evidence_refs`, `signatory`, `deadline` |
| `SecurityEventReport` | Blocked/contained threat-report request | `source_ip`, `asn`, `endpoint`, `waf_rule`, `exposure_status` |
| `DelegationNote` | Human-readable message awaiting dispatch | `recipient_group`, `message_body`, `approval_state` |

All objects carry `classification`, `compartments`, `coalition_scope`, `lineage`, `policy_bundle_hash`, and `created_at` so Gotham investigations, Foundry pipelines, and AIP agents share the same truth model.

## AI and Agent Design

Priority Sequence Alpha uses five bounded agents:

1. **Calendar Resolution Agent**: searches authorized calendars for exact event matches and returns `BLOCKED_UNRESOLVED_SOURCE` when event IDs are absent.
2. **Security Report Agent**: drafts a localized threat report from telemetry and WAF logs, classifying it as `Security Event — Blocked / Contained` unless escalation evidence exists.
3. **Risk Signoff Agent**: checks minimum data access, subprocessors, compliance evidence, incident notification, and deletion obligations.
4. **Delegation Draft Agent**: prepares the Q3 Budget Review delegation note without sending until approved.
5. **Architecture Sync Brief Agent**: converts migration-risk context into blocker-removal and dependency-compression talking points.

Operational actions use explicit approval gates: send message, sign document, reschedule event, notify external parties, or modify policy.

## Self-Improvement Loop

Each execution packet becomes a learning artifact:

```text
operator_packet
  -> resolution_attempts
  -> blocked_action_reason
  -> operator_final_action
  -> outcome_label
  -> eval_example
  -> candidate_prompt_or_workflow_update
  -> human review
  -> Apollo canary
```

The platform improves safely by learning better disambiguation prompts, event-resolution heuristics, and checklist validators. It cannot learn new goals or grant itself authority. Failed calendar resolution becomes a regression eval requiring future agents to ask for event IDs rather than hallucinate calendar edits.

## Full-Stack Implementation

```python
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4


class ActionState(StrEnum):
    READY_TO_AUTHORIZE = "ready_to_authorize"
    REQUIRES_REVIEW = "requires_review"
    BLOCKED = "blocked"
    APPROVED = "approved"
    ESCALATED = "escalated"


@dataclass(frozen=True)
class PolicyContext:
    operator_id: str
    clearance_rank: int
    compartments: frozenset[str]
    mission_ids: frozenset[UUID]
    allowed_actions: frozenset[str]


@dataclass
class CommandPacket:
    packet_id: UUID
    created_at: datetime
    organization: str
    priority_order: list[str]
    deadline_utc: datetime | None
    status: ActionState
    lineage: dict[str, Any] = field(default_factory=dict)


def build_priority_alpha_packet(deadline_utc: datetime | None) -> CommandPacket:
    return CommandPacket(
        packet_id=uuid4(),
        created_at=datetime.now(timezone.utc),
        organization="ClearGlassInc Artemis",
        priority_order=[
            "send_security_report_authorization",
            "open_apex_risk_assessment",
            "verify_five_signoff_controls",
            "sign_or_escalate_before_deadline",
            "attend_engineering_architecture_sync",
            "send_budget_review_delegation_note",
        ],
        deadline_utc=deadline_utc,
        status=ActionState.REQUIRES_REVIEW,
        lineage={"source": "operator_execution_packet", "authority": "human_required"},
    )
```

### Policy check

```python
def can_execute(ctx: PolicyContext, action: str, mission_id: UUID) -> bool:
    return action in ctx.allowed_actions and mission_id in ctx.mission_ids


def require_human_gate(action: str) -> bool:
    return action in {
        "send_external_message",
        "sign_risk_assessment",
        "reschedule_calendar_event",
        "change_model_router",
        "promote_prompt_version",
    }
```

### Workflow state machine

```python
def advance_packet(packet: CommandPacket, resolved: dict[str, bool]) -> ActionState:
    if not resolved.get("calendar_events_found", False):
        packet.lineage["calendar_status"] = "blocked_no_matching_primary_calendar_events"
    if not resolved.get("risk_document_access", False):
        return ActionState.REQUIRES_REVIEW
    if resolved.get("all_signoff_controls_pass", False):
        return ActionState.READY_TO_AUTHORIZE
    return ActionState.ESCALATED
```

## Security and Governance

- Need-to-know checks run before every document, calendar, case, and telemetry lookup.
- Row, column, object, and entity-level filters are applied before AIP sees retrieved context.
- Coalition boundaries are enforced by policy, not by prompt text.
- All blocked actions record a reason, policy hash, requested action, source system, and operator context.
- Apollo can roll back prompt packs, workflow packs, and policy bundles independently.

## Code Examples

### FastAPI endpoint for command-packet creation

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/command-packets", tags=["command-packets"])


class PacketRequest(BaseModel):
    deadline_utc: datetime | None = None
    mission_id: UUID


@router.post("/priority-alpha")
async def create_priority_alpha(req: PacketRequest, ctx: PolicyContext) -> dict[str, Any]:
    if not can_execute(ctx, "create_command_packet", req.mission_id):
        raise HTTPException(status_code=403, detail="Not authorized for mission command packet")

    packet = build_priority_alpha_packet(req.deadline_utc)
    return {
        "packet_id": str(packet.packet_id),
        "status": packet.status,
        "priority_order": packet.priority_order,
        "human_gate_required": True,
    }
```

### Eval for blocked calendar mutation

```python
def test_calendar_agent_blocks_without_event_ids(calendar_agent):
    result = calendar_agent.resolve(
        query="Q3 Budget Review and Engineering Architecture Sync at 15:30 EDT",
        primary_calendar_events=[],
    )

    assert result.status == "BLOCKED_UNRESOLVED_SOURCE"
    assert result.proposed_mutations == []
    assert "event IDs" in result.operator_next_step
```

## Scenario Walkthrough

At 14:12 EDT, a blocked external staging-server access attempt arrives through the cyber telemetry stream. Foundry normalizes the event, links it to a `CyberAsset`, and exposes it through the Ontology. The AIP Security Report Agent enriches the source IP, ASN, geolocation, endpoint, WAF rule, authentication result, and related failures in the prior 24 hours. The Compliance Agent verifies the operator can view all cited evidence, then drafts a contained-event report.

At 15:30 EDT, the Calendar Resolution Agent attempts to resolve the stated Q3 Budget Review and Engineering Architecture Sync conflict. Because no matching primary-calendar events are found, it refuses to reschedule anything and writes `BLOCKED_UNRESOLVED_SOURCE` to the audit ledger. The operator receives a manual packet: authorize the security report, open the Apex assessment, verify five controls, sign or escalate before 16:30 EDT, attend the Architecture Sync, and send the Budget Review delegation note.

After the mission window, the operator labels the calendar failure as correct behavior. Artemis converts that label into an eval requiring future workflow versions to block calendar mutation when exact source events are missing. A prompt candidate that better asks for event IDs passes offline replay, runs in shadow mode, receives human approval, and deploys through Apollo canary with rollback ready.
