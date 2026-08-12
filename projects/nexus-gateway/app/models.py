from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class Principal(BaseModel):
    subject: str
    display_name: str
    roles: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=list)
    tenant_id: str = ""


class AIActionRequest(BaseModel):
    agent_id: str = Field(min_length=3, max_length=128, pattern=r"^[A-Za-z0-9._:-]+$")
    target_tool: str = Field(min_length=2, max_length=64, pattern=r"^[a-z0-9_:-]+$")
    payload: dict[str, Any]
    objective_hash: str = Field(min_length=64, max_length=64)

    @field_validator("objective_hash")
    @classmethod
    def validate_objective_hash(cls, value: str) -> str:
        lowered = value.lower()
        if any(ch not in "0123456789abcdef" for ch in lowered):
            raise ValueError("objective_hash must be a 64-character SHA-256 hex digest")
        return lowered


class TelemetryEvent(BaseModel):
    source: str = Field(min_length=2, max_length=128)
    event_type: str = Field(min_length=2, max_length=128)
    severity: Literal["debug", "info", "warning", "high", "critical"] = "info"
    details: dict[str, Any] = Field(default_factory=dict)
    observed_at: datetime | None = None


class AegisDispatchRequest(BaseModel):
    mode: Literal["Audit", "Hunt", "Enterprise", "Baseline", "Report"] = "Audit"
    scan_minutes: int = Field(default=15, ge=1, le=1440)
    generate_report: bool = True
