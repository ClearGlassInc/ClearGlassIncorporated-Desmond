"""Bounded, privacy-minimized browser security-report intake."""
from __future__ import annotations

import json
import logging
import urllib.parse
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status

from ..security import rate_limit

router = APIRouter(prefix="/api/security", tags=["security-reports"])
logger = logging.getLogger("clearglass.security_reports")

MAX_REPORT_BYTES = 16 * 1024
ALLOWED_CONTENT_TYPES = {
    "application/csp-report",
    "application/json",
    "application/reports+json",
}


def _origin(value: Any) -> str:
    """Retain a normalized web origin, never a path, query, userinfo, or fragment."""
    if not isinstance(value, str) or len(value) > 2048:
        return ""
    keyword = value.strip().lower()
    if keyword in {"inline", "eval", "data", "blob"}:
        return keyword
    parsed = urllib.parse.urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return parsed.scheme if parsed.scheme in {"data", "blob", "inline", "eval"} else ""
    try:
        port = f":{parsed.port}" if parsed.port else ""
    except ValueError:
        return ""
    hostname = parsed.hostname.lower()
    authority = f"[{hostname}]" if ":" in hostname else hostname
    return f"{parsed.scheme.lower()}://{authority}{port}"


def _bounded_text(value: Any, limit: int = 160) -> str:
    if not isinstance(value, str):
        return ""
    return value[:limit]


def normalize_reports(payload: Any) -> list[dict[str, Any]]:
    """Normalize legacy CSP and Reporting API payloads to non-identifying fields."""
    candidates: list[dict[str, Any]] = []
    if isinstance(payload, dict) and isinstance(payload.get("csp-report"), dict):
        candidates.append(payload["csp-report"])
    elif isinstance(payload, list):
        for item in payload[:20]:
            if not isinstance(item, dict) or item.get("type") != "csp-violation":
                continue
            body = item.get("body")
            if isinstance(body, dict):
                candidates.append(body)
    elif isinstance(payload, dict):
        candidates.append(payload)

    normalized = []
    for report in candidates[:20]:
        normalized.append(
            {
                "document_origin": _origin(report.get("document-uri") or report.get("documentURL")),
                "blocked_origin": _origin(report.get("blocked-uri") or report.get("blockedURL")),
                "effective_directive": _bounded_text(
                    report.get("effective-directive") or report.get("effectiveDirective")
                ),
                "violated_directive": _bounded_text(
                    report.get("violated-directive") or report.get("violatedDirective")
                ),
                "disposition": _bounded_text(report.get("disposition"), 32),
                "status_code": report.get("status-code")
                if isinstance(report.get("status-code"), int)
                else report.get("statusCode")
                if isinstance(report.get("statusCode"), int)
                else None,
            }
        )
    return normalized


async def _read_bounded_body(request: Request) -> bytes:
    declared = request.headers.get("content-length")
    if declared:
        try:
            if int(declared) > MAX_REPORT_BYTES:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid content-length") from exc

    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > MAX_REPORT_BYTES:
            raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)
    return bytes(body)


@router.post(
    "/csp-report",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(rate_limit("csp-report", "rate_limit_csp_reports_per_minute"))],
)
async def csp_report(request: Request) -> Response:
    """Accept CSP reports without persisting URLs, queries, snippets, or client IPs."""
    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
    body = await _read_bounded_body(request)
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="invalid JSON report") from exc

    reports = normalize_reports(payload)
    if not reports:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="no CSP violations found")
    for report in reports:
        logger.info("csp_violation %s", json.dumps(report, sort_keys=True, separators=(",", ":")))
    return Response(status_code=status.HTTP_204_NO_CONTENT)
