from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class BranchRequest(BaseModel):
    installation_id: int = Field(gt=0)
    branch: str = Field(min_length=1, max_length=200, pattern=r"^[A-Za-z0-9._/-]+$")
    base_ref: str = Field(default="main", min_length=1, max_length=200)


class PullRequestRequest(BaseModel):
    installation_id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=256)
    body: str = Field(default="", max_length=65536)
    head: str = Field(min_length=1, max_length=200)
    base: str = Field(default="main", min_length=1, max_length=200)
    draft: bool = True


class WorkflowDispatchRequest(BaseModel):
    installation_id: int = Field(gt=0)
    workflow_id: str = Field(min_length=1, max_length=250)
    ref: str = Field(default="main", min_length=1, max_length=200)
    inputs: dict[str, str] = Field(default_factory=dict)
    approval_id: str = Field(min_length=1, max_length=100)


class DeploymentRequest(BaseModel):
    installation_id: int = Field(gt=0)
    ref: str = Field(default="main", min_length=1, max_length=200)
    environment: str = Field(min_length=1, max_length=100)
    description: str = Field(default="", max_length=1000)
    payload: dict[str, Any] = Field(default_factory=dict)
    approval_id: str = Field(min_length=1, max_length=100)


class ApprovalCreateRequest(BaseModel):
    action: Literal["workflow_dispatch", "deployment"]
    payload: dict[str, Any]
