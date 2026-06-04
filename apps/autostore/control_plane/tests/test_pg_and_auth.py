"""Migration-runner helpers (DB-free) + API role-auth tests."""
from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from autostore.pg_store import discover_migrations, split_sql


def test_discover_migrations_sorts_by_numeric_prefix(tmp_path):
    (tmp_path / "010_late.sql").write_text("SELECT 1;")
    (tmp_path / "002_mid.sql").write_text("SELECT 1;")
    (tmp_path / "001_init.sql").write_text("SELECT 1;")
    (tmp_path / "notes.txt").write_text("ignore me")
    names = [p.name for p in discover_migrations(tmp_path)]
    assert names == ["001_init.sql", "002_mid.sql", "010_late.sql"]


def test_real_init_migration_splits_into_statements():
    mig = pathlib.Path(__file__).resolve().parents[2] / "db" / "migrations" / "001_init.sql"
    stmts = split_sql(mig.read_text())
    # several CREATE TABLE statements + REVOKE + INSERT
    assert sum(1 for s in stmts if s.upper().startswith("CREATE TABLE")) >= 6
    assert any(s.upper().startswith("REVOKE") for s in stmts)
    # comments stripped
    assert all(not s.startswith("--") for s in stmts)


def test_split_sql_ignores_comment_lines():
    text = "-- a comment\nCREATE TABLE x (id int);\n-- another\nSELECT 1;"
    stmts = split_sql(text)
    assert stmts == ["CREATE TABLE x (id int)", "SELECT 1"]


# --- API auth (skipped cleanly if fastapi not installed) -------------------

def test_api_requires_approver_token():
    try:
        from fastapi.testclient import TestClient
        from autostore.app import app
    except Exception:
        import pytest
        pytest.skip("fastapi not installed")
    c = TestClient(app)
    # create an ESCALATE so there is something to approve
    c.post("/v1/events", json={"type": "price_recommendation",
           "payload": {"sku": "SKU-RIDGE-01", "new_price_cents": 5500}})
    pid = c.get("/v1/approvals/pending").json()[0]["id"]
    # no token -> 401
    assert c.post(f"/v1/approvals/{pid}/approve").status_code == 401
    # bad token -> 401
    assert c.post(f"/v1/approvals/{pid}/approve",
                  headers={"X-Approver-Token": "nope"}).status_code == 401
    # valid token -> 200 + approver echoed
    ok = c.post(f"/v1/approvals/{pid}/approve",
                headers={"X-Approver-Token": "demo-ops-token"})
    assert ok.status_code == 200 and ok.json()["approver"] == "ops-lead"
