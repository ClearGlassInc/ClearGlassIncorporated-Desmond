from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def canonical_hash(payload: dict[str, Any]) -> str:
    body = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(body.encode("utf-8")).hexdigest()


class Store:
    def __init__(self, path: str) -> None:
        self.path = path
        self._lock = threading.Lock()

    def _connect(self) -> sqlite3.Connection:
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.path, timeout=5)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA foreign_keys=ON")
        return con

    def init(self) -> None:
        with self._connect() as con:
            con.executescript(
                """
                CREATE TABLE IF NOT EXISTS webhook_deliveries (
                    delivery_id TEXT PRIMARY KEY,
                    event_name TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    received_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    details_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS approvals (
                    id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    status TEXT NOT NULL CHECK(status IN ('pending','approved','consumed','rejected')),
                    created_at TEXT NOT NULL,
                    approved_at TEXT,
                    consumed_at TEXT
                );
                """
            )

    def record_delivery(self, delivery_id: str, event_name: str, body: bytes) -> bool:
        digest = hashlib.sha256(body).hexdigest()
        with self._lock, self._connect() as con:
            try:
                con.execute(
                    "INSERT INTO webhook_deliveries(delivery_id,event_name,payload_sha256,received_at) VALUES(?,?,?,?)",
                    (delivery_id, event_name, digest, _utc_now()),
                )
            except sqlite3.IntegrityError:
                return False
        return True

    def audit(self, event_type: str, actor: str, details: dict[str, Any]) -> None:
        data = json.dumps(details, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO audit_events(event_type,actor,details_json,created_at) VALUES(?,?,?,?)",
                (event_type, actor, data, _utc_now()),
            )

    def recent_audit(self, limit: int = 50) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 200))
        with self._connect() as con:
            rows = con.execute(
                "SELECT id,event_type,actor,details_json,created_at FROM audit_events ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "event_type": row["event_type"],
                "actor": row["actor"],
                "details": json.loads(row["details_json"]),
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def create_approval(self, action: str, payload: dict[str, Any]) -> str:
        approval_id = str(uuid.uuid4())
        with self._lock, self._connect() as con:
            con.execute(
                "INSERT INTO approvals(id,action,payload_sha256,status,created_at) VALUES(?,?,?,?,?)",
                (approval_id, action, canonical_hash(payload), "pending", _utc_now()),
            )
        return approval_id

    def approve(self, approval_id: str) -> bool:
        with self._lock, self._connect() as con:
            cur = con.execute(
                "UPDATE approvals SET status='approved', approved_at=? WHERE id=? AND status='pending'",
                (_utc_now(), approval_id),
            )
            return cur.rowcount == 1

    def consume_approval(self, approval_id: str, action: str, payload: dict[str, Any]) -> bool:
        digest = canonical_hash(payload)
        with self._lock, self._connect() as con:
            row = con.execute(
                "SELECT action,payload_sha256,status FROM approvals WHERE id=?",
                (approval_id,),
            ).fetchone()
            if row is None:
                return False
            if row["action"] != action or row["payload_sha256"] != digest or row["status"] != "approved":
                return False
            cur = con.execute(
                "UPDATE approvals SET status='consumed', consumed_at=? WHERE id=? AND status='approved'",
                (_utc_now(), approval_id),
            )
            return cur.rowcount == 1
