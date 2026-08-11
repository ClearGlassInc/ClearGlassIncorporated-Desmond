"""Validated public-form relay, enabled only behind the authenticated edge origin."""
from __future__ import annotations

import logging
import re
import uuid
from typing import Literal

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator

from ..config import get_settings
from ..security import rate_limit

router = APIRouter(prefix="/api/forms", tags=["public-forms"])
logger = logging.getLogger("clearglass.public_forms")
EMAIL = re.compile(r"^[^\s@]{1,64}@[^\s@]{1,190}\.[^\s@]{2,63}$")


class PublicFormSubmission(BaseModel):
    kind: Literal["homepage-subscribe", "hardening-sprint", "phipa-checklist"]
    email: str = Field(min_length=3, max_length=254)
    name: str = Field(default="", max_length=120)
    organization: str = Field(default="", max_length=160)
    size: str = Field(default="", max_length=80)
    message: str = Field(default="", max_length=4000)
    consent: bool
    website: str = Field(default="", max_length=200, description="Honeypot; real users leave blank.")

    @field_validator("email")
    @classmethod
    def valid_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if EMAIL.fullmatch(normalized) is None:
            raise ValueError("invalid email address")
        return normalized

    @field_validator("name", "organization", "size", "message", "website")
    @classmethod
    def trim_text(cls, value: str) -> str:
        return value.strip()


class AcceptedSubmission(BaseModel):
    accepted: bool
    submission_id: str


@router.post(
    "/submit",
    response_model=AcceptedSubmission,
    status_code=status.HTTP_202_ACCEPTED,
    dependencies=[Depends(rate_limit("public-form", "rate_limit_public_forms_per_minute"))],
)
async def submit_form(submission: PublicFormSubmission) -> AcceptedSubmission:
    settings = get_settings()
    if not settings.public_forms_enabled:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="form intake unavailable")
    submission_id = str(uuid.uuid4())
    if submission.website:
        # Give bots an indistinguishable success without forwarding their payload.
        logger.info("public_form_honeypot kind=%s id=%s", submission.kind, submission_id)
        return AcceptedSubmission(accepted=True, submission_id=submission_id)
    if not submission.consent:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="contact consent is required")

    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "Idempotency-Key": submission_id,
        "User-Agent": "ClearGlass-Control-Plane/1",
    }
    if settings.public_form_relay_bearer_token:
        headers["Authorization"] = f"Bearer {settings.public_form_relay_bearer_token}"
    payload = submission.model_dump(exclude={"website"})
    payload["submission_id"] = submission_id
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=False) as client:
            response = await client.post(settings.public_form_relay_url, json=payload, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as exc:
        logger.warning(
            "public_form_relay_failed kind=%s id=%s error=%s",
            submission.kind,
            submission_id,
            type(exc).__name__,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="form relay unavailable",
        ) from exc
    logger.info("public_form_relayed kind=%s id=%s", submission.kind, submission_id)
    return AcceptedSubmission(accepted=True, submission_id=submission_id)
