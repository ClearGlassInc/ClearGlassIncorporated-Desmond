"""Operator CLI for connecting the Etsy shop: ``python -m app.etsy_connect``.

Connecting a shop is a human act — Etsy will only mint a token after the shop owner
approves the requested scopes in a browser. This CLI drives that handshake and hands
back the env vars the control plane needs. It is the one and only path from "we have an
Etsy app" to "``/etsy/connection`` reports connected".

    python -m app.etsy_connect              # full consent flow (prints URL, takes the redirect)
    python -m app.etsy_connect --status     # what is configured, what is missing
    python -m app.etsy_connect --refresh    # new access token from the stored refresh token
    python -m app.etsy_connect --exchange --code ... --verifier ...   # split-machine exchange

Nothing here writes to Etsy and nothing here persists a secret: the tokens are printed
once for the operator to paste into their secret store (Render env group, GitHub Actions
secret, local ``.env`` that is *not* committed).
"""
from __future__ import annotations

import argparse
import sys
import urllib.parse

from .config import get_settings
from .etsy import REQUIRED_SCOPES, connection_status
from .etsy_oauth import (
    EtsyOAuthError,
    build_authorize_url,
    env_exports,
    exchange_code,
    generate_pkce,
    generate_state,
    refresh_access_token,
)


def _print_status() -> int:
    """Show what is configured for the connection, and the first thing still blocking it."""
    settings = get_settings()
    status = connection_status(settings)
    print("Etsy connection")
    print(f"  state           : {status['state']}")
    print(f"  declared profile: {status['shop']['declared_profile_url'] or '(none)'}")
    print(f"  shop id         : {status['shop']['shop_id'] or '(unknown until connected)'}")
    print(f"  keystring set   : {'yes' if settings.etsy_keystring else 'NO'}")
    print(f"  redirect uri    : {settings.etsy_redirect_uri or 'NOT SET'}")
    print(f"  granted scopes  : {', '.join(status['granted_scopes']) or '(none)'}")
    if status["scope_gap"]:
        print(f"  missing scopes  : {', '.join(status['scope_gap'])}")
    for item in status["missing"]:
        print(f"  missing         : {item}")
    print(f"\n{status['next_step']}")
    return 0 if status["connected"] else 1


def _code_from_input(raw: str) -> str:
    """Accept either the bare ``code`` or the whole redirect URL pasted from the browser."""
    raw = raw.strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        query = urllib.parse.urlparse(raw).query
        params = urllib.parse.parse_qs(query)
        if "error" in params:
            raise EtsyOAuthError(f"Etsy returned an error on the redirect: {params['error'][0]}")
        if "code" not in params:
            raise EtsyOAuthError("That redirect URL has no ?code= parameter.")
        return params["code"][0]
    return raw


def _print_tokens(tokens: dict, scopes: tuple[str, ...]) -> None:
    print("\nConnected. Set these as RUNTIME env vars (never commit them):\n")
    print(env_exports(tokens, scopes))
    if tokens.get("expires_in"):
        print(f"\n# access token expires in {tokens['expires_in']}s — "
              f"re-run with --refresh (or automate it) before it lapses")
    print("\nThen restart the control plane and POST /etsy/verify to confirm "
          "shop identity, listing/order permissions, and sync status.")


def _run_consent_flow(scopes: tuple[str, ...], code: str | None, verifier: str | None) -> int:
    settings = get_settings()

    if code and verifier:
        # Split-machine path: the browser half happened elsewhere.
        tokens = exchange_code(_code_from_input(code), verifier, settings)
        _print_tokens(tokens, scopes)
        return 0

    verifier, challenge = generate_pkce()
    state = generate_state()
    url = build_authorize_url(settings, code_challenge=challenge, state=state, scopes=scopes)

    print("1. Open this URL as the Etsy shop owner and approve the requested scopes:\n")
    print(f"   {url}\n")
    print(f"2. Etsy redirects to {settings.etsy_redirect_uri} with ?code=...&state=...")
    print(f"   Confirm the returned state is exactly: {state}")
    print("   (If it differs, abandon the flow — the response is not ours.)\n")
    print("   Keep this verifier if you need to finish the exchange elsewhere:")
    print(f"   --verifier {verifier}\n")

    try:
        raw = input("3. Paste the full redirect URL (or just the code): ")
    except (EOFError, KeyboardInterrupt):
        print("\nAborted — nothing was connected.", file=sys.stderr)
        return 1

    tokens = exchange_code(_code_from_input(raw), verifier, settings)
    _print_tokens(tokens, scopes)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.etsy_connect",
        description="Connect the ClearGlass Etsy shop via OAuth2 PKCE (read-only setup; "
                    "all shop writes stay behind the approval gate).",
    )
    parser.add_argument("--status", action="store_true", help="report connection state and exit")
    parser.add_argument("--refresh", action="store_true", help="mint a new access token from the refresh token")
    parser.add_argument("--exchange", action="store_true", help="exchange a code obtained elsewhere")
    parser.add_argument("--code", help="authorization code, or the full redirect URL")
    parser.add_argument("--verifier", help="PKCE code_verifier from the authorize step")
    parser.add_argument(
        "--scopes",
        default=",".join(REQUIRED_SCOPES),
        help="comma-separated OAuth scopes to request (default: the scopes this operator needs)",
    )
    args = parser.parse_args(argv)
    scopes = tuple(s.strip() for s in args.scopes.split(",") if s.strip())

    try:
        if args.status:
            return _print_status()
        if args.refresh:
            tokens = refresh_access_token(settings=get_settings())
            _print_tokens(tokens, scopes)
            return 0
        if args.exchange and not (args.code and args.verifier):
            parser.error("--exchange requires both --code and --verifier")
        return _run_consent_flow(scopes, args.code, args.verifier)
    except EtsyOAuthError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
