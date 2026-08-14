from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_env: str
    github_app_id: str
    github_private_key: str
    github_webhook_secret: str
    admin_api_key: str
    database_path: str
    github_api_url: str
    allowed_org: str
    request_timeout_seconds: float
    max_body_bytes: int

    @classmethod
    def load(cls) -> "Settings":
        private_key = os.getenv("GITHUB_PRIVATE_KEY", "").replace("\\n", "\n").strip()
        return cls(
            app_env=os.getenv("APP_ENV", "development").strip().lower(),
            github_app_id=os.getenv("GITHUB_APP_ID", "").strip(),
            github_private_key=private_key,
            github_webhook_secret=os.getenv("GITHUB_WEBHOOK_SECRET", "").strip(),
            admin_api_key=os.getenv("ADMIN_API_KEY", "").strip(),
            database_path=os.getenv("DATABASE_PATH", "./data/controller.sqlite3").strip(),
            github_api_url=os.getenv("GITHUB_API_URL", "https://api.github.com").rstrip("/"),
            allowed_org=os.getenv("GITHUB_ALLOWED_ORG", "ClearGlassInc").strip(),
            request_timeout_seconds=float(os.getenv("REQUEST_TIMEOUT_SECONDS", "12")),
            max_body_bytes=int(os.getenv("MAX_BODY_BYTES", "1048576")),
        )

    @property
    def missing_required(self) -> list[str]:
        required = {
            "GITHUB_APP_ID": self.github_app_id,
            "GITHUB_PRIVATE_KEY": self.github_private_key,
            "GITHUB_WEBHOOK_SECRET": self.github_webhook_secret,
            "ADMIN_API_KEY": self.admin_api_key,
        }
        return [name for name, value in required.items() if not value]

    @property
    def ready(self) -> bool:
        return not self.missing_required
