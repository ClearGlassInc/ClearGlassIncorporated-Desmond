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

    # Per-client-IP sliding-window request limits (per minute); 0 disables a throttle.
    rate_limit_checkout_per_minute: int = 30
    rate_limit_webhook_per_minute: int = 240
    rate_limit_decisions_per_minute: int = 60

    # Payments (never logged, never echoed in responses)
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_publishable_key: str = ""

    escalation_email: str = "info@clearglassinc.com"
    slack_webhook_url: str = ""

    # Etsy Open API v3 connection (never logged; secrets are runtime env vars only).
    # A connection is "present" once keystring + access token are set; identity and
    # permissions are confirmed by a read-only verification call (see app/etsy.py).
    etsy_keystring: str = ""          # app API key (x-api-key header)
    etsy_shared_secret: str = ""      # OAuth app shared secret (never echoed)
    etsy_access_token: str = ""       # OAuth2 access token, format "<user_id>.<token>"
    etsy_refresh_token: str = ""      # OAuth2 refresh token (access tokens expire hourly)
    etsy_shop_id: str = ""            # numeric shop id; derived from the token if blank
    etsy_shop_name: str = ""          # declared shop name, cross-checked on verify
    etsy_login_email: str = ""        # declared Etsy account email (informational)
    # Comma-separated OAuth scopes granted at token-exchange time.
    etsy_scopes: str = ""
    etsy_api_base: str = "https://openapi.etsy.com/v3"


@lru_cache
def get_settings() -> Settings:
    """Cached settings singleton."""
    return Settings()
