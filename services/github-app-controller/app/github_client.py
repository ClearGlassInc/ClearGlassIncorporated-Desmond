from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx
import jwt

from .config import Settings


class GitHubAPIError(RuntimeError):
    pass


class GitHubClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def _app_jwt(self) -> str:
        if not self.settings.github_app_id or not self.settings.github_private_key:
            raise GitHubAPIError("GitHub App credentials are not configured.")
        now = int(time.time())
        payload = {"iat": now - 60, "exp": now + 540, "iss": self.settings.github_app_id}
        return jwt.encode(payload, self.settings.github_private_key, algorithm="RS256")

    def _headers(self, bearer: str) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {bearer}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "ClearGlass-GitHub-Controller/1.0",
        }

    async def _request(self, method: str, path: str, bearer: str, *, json_body: dict[str, Any] | None = None, expected: tuple[int, ...] = (200,)) -> Any:
        url = f"{self.settings.github_api_url}{path}"
        timeout = httpx.Timeout(self.settings.request_timeout_seconds)
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.request(method, url, headers=self._headers(bearer), json=json_body)
        if response.status_code not in expected:
            request_id = response.headers.get("x-github-request-id", "unknown")
            raise GitHubAPIError(f"GitHub API request failed with status {response.status_code}; request_id={request_id}")
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    async def installation_token(self, installation_id: int) -> str:
        data = await self._request("POST", f"/app/installations/{installation_id}/access_tokens", self._app_jwt(), expected=(201,))
        token = data.get("token") if isinstance(data, dict) else None
        if not token:
            raise GitHubAPIError("GitHub did not return an installation token.")
        return token

    async def list_installations(self) -> Any:
        return await self._request("GET", "/app/installations?per_page=100", self._app_jwt())

    async def actions_status(self, installation_id: int, owner: str, repo: str) -> Any:
        token = await self.installation_token(installation_id)
        return await self._request("GET", f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/actions/runs?per_page=20", token)

    async def create_branch(self, installation_id: int, owner: str, repo: str, branch: str, base_ref: str) -> Any:
        token = await self.installation_token(installation_id)
        owner_q, repo_q = quote(owner, safe=""), quote(repo, safe="")
        ref = await self._request("GET", f"/repos/{owner_q}/{repo_q}/git/ref/heads/{quote(base_ref, safe='')}", token)
        sha = ref["object"]["sha"]
        return await self._request("POST", f"/repos/{owner_q}/{repo_q}/git/refs", token, json_body={"ref": f"refs/heads/{branch}", "sha": sha}, expected=(201,))

    async def create_pull_request(self, installation_id: int, owner: str, repo: str, *, title: str, body: str, head: str, base: str, draft: bool) -> Any:
        token = await self.installation_token(installation_id)
        return await self._request("POST", f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/pulls", token, json_body={"title": title, "body": body, "head": head, "base": base, "draft": draft}, expected=(201,))

    async def dispatch_workflow(self, installation_id: int, owner: str, repo: str, workflow_id: str, ref: str, inputs: dict[str, str]) -> None:
        token = await self.installation_token(installation_id)
        await self._request("POST", f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/actions/workflows/{quote(workflow_id, safe='')}/dispatches", token, json_body={"ref": ref, "inputs": inputs}, expected=(204,))

    async def create_deployment(self, installation_id: int, owner: str, repo: str, *, ref: str, environment: str, description: str, payload: dict[str, Any]) -> Any:
        token = await self.installation_token(installation_id)
        return await self._request("POST", f"/repos/{quote(owner, safe='')}/{quote(repo, safe='')}/deployments", token, json_body={"ref": ref, "environment": environment, "description": description, "payload": payload, "auto_merge": False, "required_contexts": []}, expected=(201,))
