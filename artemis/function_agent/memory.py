# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
"""Durable namespaced memory for agent state and checkpoints."""
from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any


class SQLiteMemory:
    """Small durable memory store with namespace isolation and TTL support."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def set(self, namespace: str, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        now = datetime.now(UTC)
        expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None
        payload = json.dumps(value, sort_keys=True, default=str)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO agent_memory(namespace, key, value, expires_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(namespace, key) DO UPDATE SET
                    value=excluded.value,
                    expires_at=excluded.expires_at,
                    updated_at=excluded.updated_at
                """,
                (
                    namespace,
                    key,
                    payload,
                    expires_at.isoformat() if expires_at else None,
                    now.isoformat(),
                ),
            )

    def get(self, namespace: str, key: str, default: Any = None) -> Any:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT value, expires_at FROM agent_memory WHERE namespace=? AND key=?",
                (namespace, key),
            ).fetchone()
            if row is None:
                return default
            if row[1] and datetime.fromisoformat(row[1]) < datetime.now(UTC):
                connection.execute(
                    "DELETE FROM agent_memory WHERE namespace=? AND key=?", (namespace, key)
                )
                return default
            return json.loads(row[0])

    def delete(self, namespace: str, key: str) -> bool:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM agent_memory WHERE namespace=? AND key=?", (namespace, key)
            )
            return cursor.rowcount > 0

    def list_namespace(self, namespace: str, limit: int = 100) -> dict[str, Any]:
        self.prune_expired()
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT key, value FROM agent_memory WHERE namespace=? ORDER BY updated_at DESC LIMIT ?",
                (namespace, limit),
            ).fetchall()
        return {key: json.loads(value) for key, value in rows}

    def prune_expired(self) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM agent_memory WHERE expires_at IS NOT NULL AND expires_at < ?",
                (datetime.now(UTC).isoformat(),),
            )
            return cursor.rowcount

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS agent_memory(
                    namespace TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    expires_at TEXT,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY(namespace, key)
                )
                """
            )
            connection.execute(
                "CREATE INDEX IF NOT EXISTS idx_agent_memory_expiry ON agent_memory(expires_at)"
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, timeout=10)
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")
        return connection
