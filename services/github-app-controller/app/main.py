from __future__ import annotations

import hashlib
from typing import Any

from fastapi import FastAPI, Header, HTTPException, Query, Request, status
from fastapi.responses import JSONResponse

from .config import Settings
from .github_client import GitHubAPIError, GitHubClient
from .models import ApprovalCreateRequest, BranchRequest, DeploymentRequest, PullRequestRequest, WorkflowDispatchRequest
from .security import require_admin, verify_webhook_signature
from .store import Store

settings = Settings.load()
store = Store(settings.database_path)
store.init()
github = GitHubClient(settings)

app = FastAPI(title="ClearGlass Engineering Controller", version="0.1.0", docs_url="/docs" if settings.app_env != "production" else None, redoc_url=None)


def _guard(authorization: str | None) -> None:
    require_admin(settings, authorization)


def _enforce_org(owner: str) -> None:
    if settings.allowed_org and owner.lower() != settings.allowed_org.lower():
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Repository owner is not allowed.")


@app.exception_handler(GitHubAPIError)
async def github_error_handler(_: Request, exc: GitHubAPIError) -> JSONResponse:
    store.audit("github_api_error", "controller", {"error": str(exc)})
    return JSONResponse(status_code=status.HTTP_502_BAD_GATEWAY, content={"detail": "GitHub API operation failed.", "diagnostic": str(exc)})


@app.get("/")
async def root() -> dict[str, Any]:
    return {"service": "ClearGlass Engineering Controller", "version": app.version, "environment": settings.app_env, "ready": settings.ready, "missing_configuration": settings.missing_required}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> JSONResponse:
    code = status.HTTP_200_OK if settings.ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=code, content={"ready": settings.ready, "missing_configuration": settings.missing_required, "allowed_org": settings.allowed_org})


@app.post("/github/webhook")
async def github_webhook(request: Request, x_hub_signature_256: str | None = Header(default=None), x_github_event: str | None = Header(default=None), x_github_delivery: str | None = Header(default=None)) -> JSONResponse:
    content_length = request.headers.get("content-length")
    if content_length and content_length.isdigit() and int(content_length) > settings.max_body_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large.")
    body = await request.body()
    if len(body) > settings.max_body_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Payload too large.")
    if not verify_webhook_signature(body, x_hub_signature_256, settings.github_webhook_secret):
        store.audit("webhook_rejected", "github", {"reason": "invalid_signature"})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid webhook signature.")
    if not x_github_event or not x_github_delivery:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing GitHub delivery headers.")
    if not store.record_delivery(x_github_delivery, x_github_event, body):
        return JSONResponse(status_code=status.HTTP_200_OK, content={"accepted": True, "duplicate": True})
    try:
        payload = await request.json()
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload.") from exc
    org = (payload.get("organization") or {}).get("login") or ((payload.get("repository") or {}).get("owner") or {}).get("login") or ""
    if settings.allowed_org and org and org.lower() != settings.allowed_org.lower():
        store.audit("webhook_rejected", "github", {"reason": "org_not_allowed", "event": x_github_event, "delivery": x_github_delivery})
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Organization is not allowed.")
    store.audit("webhook_received", "github", {"event": x_github_event, "delivery": x_github_delivery, "repository": (payload.get("repository") or {}).get("full_name"), "payload_sha256": hashlib.sha256(body).hexdigest()})
    return JSONResponse(status_code=status.HTTP_202_ACCEPTED, content={"accepted": True, "duplicate": False})


@app.get("/audit")
async def audit_log(limit: int = Query(default=50, ge=1, le=200), authorization: str | None = Header(default=None)) -> list[dict[str, Any]]:
    _guard(authorization)
    return store.recent_audit(limit)


@app.get("/github/installations")
async def installations(authorization: str | None = Header(default=None)) -> Any:
    _guard(authorization)
    return await github.list_installations()


@app.get("/github/actions/status")
async def actions_status(owner: str, repo: str, installation_id: int = Query(gt=0), authorization: str | None = Header(default=None)) -> Any:
    _guard(authorization)
    _enforce_org(owner)
    return await github.actions_status(installation_id, owner, repo)


@app.post("/approvals", status_code=status.HTTP_201_CREATED)
async def create_approval(request: ApprovalCreateRequest, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _guard(authorization)
    approval_id = store.create_approval(request.action, request.payload)
    store.audit("approval_created", "admin", {"approval_id": approval_id, "action": request.action})
    return {"approval_id": approval_id, "status": "pending"}


@app.post("/approvals/{approval_id}/approve")
async def approve(approval_id: str, authorization: str | None = Header(default=None)) -> dict[str, str]:
    _guard(authorization)
    if not store.approve(approval_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Approval is missing or not pending.")
    store.audit("approval_granted", "admin", {"approval_id": approval_id})
    return {"approval_id": approval_id, "status": "approved"}


@app.post("/github/repos/{owner}/{repo}/branch", status_code=status.HTTP_201_CREATED)
async def create_branch(owner: str, repo: str, request: BranchRequest, authorization: str | None = Header(default=None)) -> Any:
    _guard(authorization)
    _enforce_org(owner)
    result = await github.create_branch(request.installation_id, owner, repo, request.branch, request.base_ref)
    store.audit("branch_created", "admin", {"repository": f"{owner}/{repo}", "branch": request.branch, "base_ref": request.base_ref})
    return result


@app.post("/github/repos/{owner}/{repo}/pull-request", status_code=status.HTTP_201_CREATED)
async def create_pull_request(owner: str, repo: str, request: PullRequestRequest, authorization: str | None = Header(default=None)) -> Any:
    _guard(authorization)
    _enforce_org(owner)
    result = await github.create_pull_request(request.installation_id, owner, repo, title=request.title, body=request.body, head=request.head, base=request.base, draft=request.draft)
    store.audit("pull_request_created", "admin", {"repository": f"{owner}/{repo}", "head": request.head, "base": request.base, "draft": request.draft})
    return result


@app.post("/github/repos/{owner}/{repo}/dispatch", status_code=status.HTTP_202_ACCEPTED)
async def dispatch_workflow(owner: str, repo: str, request: WorkflowDispatchRequest, authorization: str | None = Header(default=None)) -> dict[str, bool]:
    _guard(authorization)
    _enforce_org(owner)
    approval_payload = {"repository": f"{owner}/{repo}", "installation_id": request.installation_id, "workflow_id": request.workflow_id, "ref": request.ref, "inputs": request.inputs}
    if not store.consume_approval(request.approval_id, "workflow_dispatch", approval_payload):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Valid approved operation is required.")
    await github.dispatch_workflow(request.installation_id, owner, repo, request.workflow_id, request.ref, request.inputs)
    store.audit("workflow_dispatched", "admin", approval_payload)
    return {"accepted": True}


@app.post("/github/repos/{owner}/{repo}/deploy", status_code=status.HTTP_201_CREATED)
async def create_deployment(owner: str, repo: str, request: DeploymentRequest, authorization: str | None = Header(default=None)) -> Any:
    _guard(authorization)
    _enforce_org(owner)
    approval_payload = {"repository": f"{owner}/{repo}", "installation_id": request.installation_id, "ref": request.ref, "environment": request.environment, "description": request.description, "payload": request.payload}
    if not store.consume_approval(request.approval_id, "deployment", approval_payload):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Valid approved operation is required.")
    result = await github.create_deployment(request.installation_id, owner, repo, ref=request.ref, environment=request.environment, description=request.description, payload=request.payload)
    store.audit("deployment_created", "admin", approval_payload)
    return result
