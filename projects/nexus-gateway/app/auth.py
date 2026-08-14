from functools import lru_cache

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from .config import Settings, get_settings
from .models import Principal

security = HTTPBearer(auto_error=True)


@lru_cache(maxsize=8)
def _jwk_client(url: str) -> PyJWKClient:
    return PyJWKClient(url, cache_keys=True, lifespan=3600)


def _extract_scopes(claims: dict) -> list[str]:
    raw = claims.get("scp", "")
    if isinstance(raw, str):
        return [part for part in raw.split() if part]
    return []


async def verify_managed_identity(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> Principal:
    token = credentials.credentials

    if settings.dev_auth_enabled:
        if token != "dev-operator":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid development token")
        return Principal(
            subject="dev-operator",
            display_name="Development Operator",
            roles=[settings.required_role],
            scopes=[settings.required_scope],
            tenant_id="development",
        )

    if not settings.entra_tenant_id or not settings.entra_audience or not settings.jwks_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Identity broker is not configured; authentication fails closed.",
        )

    try:
        signing_key = _jwk_client(settings.jwks_url).get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=settings.entra_audience,
            issuer=settings.issuer,
            options={"require": ["exp", "iat", "iss", "aud", "sub"]},
        )
    except Exception as exc:  # PyJWT emits several verification-specific exception types.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Entra ID bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    roles = claims.get("roles", [])
    if not isinstance(roles, list):
        roles = []
    scopes = _extract_scopes(claims)
    if settings.required_role not in roles and settings.required_scope not in scopes:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Principal lacks NEXUS operator authorization.",
        )

    return Principal(
        subject=str(claims.get("sub", "")),
        display_name=str(claims.get("name") or claims.get("preferred_username") or claims.get("sub", "unknown")),
        roles=[str(x) for x in roles],
        scopes=scopes,
        tenant_id=str(claims.get("tid", "")),
    )
