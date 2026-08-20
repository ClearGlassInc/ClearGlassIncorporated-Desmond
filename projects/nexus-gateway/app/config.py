from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="NEXUS_", env_file=".env", extra="ignore")

    service_name: str = "ClearGlass NEXUS Security Gateway"
    environment: str = "production"
    version: str = "12.1.0"

    entra_tenant_id: str = ""
    entra_audience: str = ""
    entra_jwks_url: str = ""
    required_role: str = "Nexus.Operator"
    required_scope: str = "nexus.execute"
    dev_auth_enabled: bool = False

    allowed_tools: str = "network_optimizer,telemetry_parser,aegis_scan"
    max_payload_bytes: Annotated[int, Field(ge=1024, le=1_048_576)] = 65_536
    telemetry_queue_size: Annotated[int, Field(ge=100, le=100_000)] = 5_000
    telemetry_history_size: Annotated[int, Field(ge=100, le=100_000)] = 1_000

    aegis_execution_enabled: bool = False
    aegis_script_path: str = ""
    aegis_powershell_executable: str = "pwsh"
    aegis_timeout_seconds: Annotated[int, Field(ge=5, le=3600)] = 900

    @property
    def tool_allowlist(self) -> frozenset[str]:
        return frozenset(x.strip() for x in self.allowed_tools.split(",") if x.strip())

    @property
    def issuer(self) -> str:
        if not self.entra_tenant_id:
            return ""
        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/v2.0"

    @property
    def jwks_url(self) -> str:
        if self.entra_jwks_url:
            return self.entra_jwks_url
        if not self.entra_tenant_id:
            return ""
        return f"https://login.microsoftonline.com/{self.entra_tenant_id}/discovery/v2.0/keys"

    @property
    def aegis_path(self) -> Path | None:
        return Path(self.aegis_script_path).expanduser().resolve() if self.aegis_script_path else None


@lru_cache
def get_settings() -> Settings:
    return Settings()
