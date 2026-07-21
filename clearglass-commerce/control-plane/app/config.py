"""Environment-driven settings for the commerce control plane."""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration, sourced from environment / .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "development"
    app_name: str = "clearglass-commerce"
    log_level: str = "info"

    database_url: str = "postgresql+psycopg://commerce:commerce@localhost:5432/commerce"
    # Create tables from ORM metadata on startup (handy for SQLite/dev/demo; prod uses migrations).
    auto_create_tables: bool = False
    # Comma-separated browser origins allowed to call the API (storefront/admin).
    cors_allow_origins: str = (
        "https://www.clearglassinc.com,"
        "https://clearglass-commerce-storefront.onrender.com,"
        "https://clearglass-commerce-admin.onrender.com,"
        "http://localhost:3000,http://localhost:3001"
    )

    # Governance
    require_approval_for_high_risk: bool = True
    inventory_low_threshold: int = 10

    # Security — bearer token required to decide approvals. Empty means: allow in
    # dev (zero-config demos/tests), refuse decisions in production (fail closed).
    admin_api_token: str = ""
    # Per-client-IP sliding-window limits (per minute); 0 disables a throttle.
    rate_limit_checkout_per_minute: int = 30
    rate_limit_webhook_per_minute: int = 240
    rate_limit_decisions_per_minute: int = 60

    # Payments (never logged, never echoed in responses)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    escalation_email: str = "info@clearglassinc.com"
    slack_webhook_url: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
