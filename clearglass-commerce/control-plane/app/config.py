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

    # Admin authentication. The approval gate is only meaningful if not everyone can
    # open it, so mutating/administrative endpoints (approvals, pricing, refunds,
    # catalog writes) require a bearer token when this is set. Unset = open dev/mock
    # mode (consistent with no-Stripe-key mock payments); production must set it or the
    # app fails closed at startup. Comma-separated to allow rotation / per-operator keys.
    admin_api_key: str = ""

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
