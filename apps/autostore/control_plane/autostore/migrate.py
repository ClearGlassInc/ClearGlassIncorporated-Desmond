"""Migrations runner CLI.

    python -m autostore.migrate           # apply pending migrations
    python -m autostore.migrate --list    # list discovered migrations (no DB)

DSN comes from DATABASE_URL. Requires psycopg only when actually applying.
"""
from __future__ import annotations

import os
import pathlib
import sys

from .pg_store import apply_migrations, discover_migrations

MIGRATIONS_DIR = pathlib.Path(__file__).resolve().parents[2] / "db" / "migrations"


def main(argv: list[str] | None = None) -> int:
    argv = argv if argv is not None else sys.argv[1:]
    if "--list" in argv:
        for p in discover_migrations(MIGRATIONS_DIR):
            print(p.name)
        return 0

    dsn = os.environ.get("DATABASE_URL")
    if not dsn:
        print("DATABASE_URL not set", file=sys.stderr)
        return 2
    try:
        import psycopg
    except ImportError:  # pragma: no cover
        print("psycopg not installed", file=sys.stderr)
        return 2
    conn = psycopg.connect(dsn)  # pragma: no cover - needs DB
    applied = apply_migrations(conn, MIGRATIONS_DIR)  # pragma: no cover
    print("applied:", ", ".join(applied) if applied else "(none — up to date)")  # pragma: no cover
    return 0  # pragma: no cover


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
