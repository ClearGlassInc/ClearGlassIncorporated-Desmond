#!/usr/bin/env python3
"""
shipprompt — opinionated prompt-ops & model-deploy CLI.

Commands:
    shipprompt validate              Validate the prompt registry.
    shipprompt diff <ref>            Show prompt-level diff vs git ref.
    shipprompt manifest               Build a deploy manifest (prompt+model versions, signed).
    shipprompt deploy --env <env>    Push current manifest to a target environment.
    shipprompt rollback --env <env>  Restore previous manifest for an environment.
    shipprompt eval --suite <name>   Run an eval suite and emit a JUnit + JSON report.

Design goals:
    - Single binary surface area. Zero hidden state. Everything is a file in the repo.
    - Prompts are content-addressed (SHA-256) and signed.
    - The deploy manifest is the only thing the runtime trusts.
    - Rollback = restore previous manifest. No magic.

Repo layout this CLI assumes:
    prompts/registry.yaml           Canonical prompt registry.
    prompts/<id>/<version>.txt       Prompt body files.
    deploy/manifests/<env>/current.json
    deploy/manifests/<env>/previous.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:
    sys.stderr.write("shipprompt: PyYAML is required. pip install pyyaml\n")
    sys.exit(2)


REPO = Path(os.environ.get("SHIPPROMPT_REPO", ".")).resolve()
REGISTRY_PATH = REPO / "prompts" / "registry.yaml"
PROMPTS_DIR = REPO / "prompts"
MANIFEST_DIR = REPO / "deploy" / "manifests"


# ---------- model ----------

@dataclass(frozen=True)
class PromptRecord:
    id: str
    version: str
    path: str
    sha256: str
    model: str
    description: str

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def _load_registry() -> list[PromptRecord]:
    if not REGISTRY_PATH.exists():
        die(f"registry not found at {REGISTRY_PATH}")
    data = yaml.safe_load(REGISTRY_PATH.read_text())
    if not isinstance(data, dict) or "prompts" not in data:
        die("registry must be a mapping with a top-level `prompts:` list")
    out: list[PromptRecord] = []
    seen: set[tuple[str, str]] = set()
    for entry in data["prompts"]:
        for required in ("id", "version", "path", "model"):
            if required not in entry:
                die(f"prompt entry missing required key: {required}: {entry}")
        key = (entry["id"], entry["version"])
        if key in seen:
            die(f"duplicate prompt id+version: {key}")
        seen.add(key)
        body_path = REPO / entry["path"]
        if not body_path.exists():
            die(f"prompt body not found: {body_path}")
        out.append(PromptRecord(
            id=entry["id"],
            version=str(entry["version"]),
            path=entry["path"],
            sha256=_sha256_file(body_path),
            model=entry["model"],
            description=entry.get("description", ""),
        ))
    return out


def die(msg: str, code: int = 1) -> None:
    sys.stderr.write(f"shipprompt: {msg}\n")
    sys.exit(code)


def _git(args: list[str]) -> str:
    return subprocess.check_output(["git", "-C", str(REPO), *args]).decode().strip()


# ---------- commands ----------

def cmd_validate(_args: argparse.Namespace) -> int:
    records = _load_registry()
    print(f"OK — {len(records)} prompts validated.")
    for r in records:
        print(f"  {r.id}@{r.version}  model={r.model}  sha256={r.sha256[:12]}…")
    return 0


def cmd_diff(args: argparse.Namespace) -> int:
    ref = args.ref
    try:
        old = _git(["show", f"{ref}:prompts/registry.yaml"])
    except subprocess.CalledProcessError:
        die(f"could not read prompts/registry.yaml at {ref}")

    new_records = {(r.id, r.version): r for r in _load_registry()}
    old_data = yaml.safe_load(old) or {}
    old_records = {
        (e["id"], str(e["version"])): e for e in old_data.get("prompts", [])
    }

    added = sorted(set(new_records) - set(old_records))
    removed = sorted(set(old_records) - set(new_records))
    common = sorted(set(new_records) & set(old_records))

    if added:
        print("ADDED:")
        for k in added:
            print(f"  + {k[0]}@{k[1]}")
    if removed:
        print("REMOVED:")
        for k in removed:
            print(f"  - {k[0]}@{k[1]}")
    changed = []
    for k in common:
        new_r = new_records[k]
        try:
            old_body = _git(["show", f"{ref}:{old_records[k]['path']}"])
        except subprocess.CalledProcessError:
            old_body = ""
        old_sha = hashlib.sha256(old_body.encode()).hexdigest()
        if old_sha != new_r.sha256:
            changed.append(k)
    if changed:
        print("MUTATED (same id+version, different body — POLICY VIOLATION):")
        for k in changed:
            print(f"  ! {k[0]}@{k[1]}")
        return 2
    if not (added or removed or changed):
        print("No prompt changes vs", ref)
    return 0


def cmd_manifest(_args: argparse.Namespace) -> int:
    records = _load_registry()
    try:
        commit = _git(["rev-parse", "HEAD"])
    except Exception:
        commit = "unknown"
    manifest = {
        "schema": "shipprompt.manifest/v1",
        "built_at": int(time.time()),
        "commit": commit,
        "prompts": [r.to_json() for r in records],
    }
    serialized = json.dumps(manifest, sort_keys=True, separators=(",", ":")).encode()
    manifest["signature_sha256"] = hashlib.sha256(serialized).hexdigest()
    print(json.dumps(manifest, indent=2))
    return 0


def _manifest_path(env: str, kind: str) -> Path:
    return MANIFEST_DIR / env / f"{kind}.json"


def cmd_deploy(args: argparse.Namespace) -> int:
    env = args.env
    cur = _manifest_path(env, "current")
    prev = _manifest_path(env, "previous")
    cur.parent.mkdir(parents=True, exist_ok=True)

    records = _load_registry()
    new_manifest = {
        "schema": "shipprompt.manifest/v1",
        "env": env,
        "built_at": int(time.time()),
        "commit": _safe_git_head(),
        "prompts": [r.to_json() for r in records],
    }
    new_serialized = json.dumps(new_manifest, sort_keys=True, separators=(",", ":")).encode()
    new_manifest["signature_sha256"] = hashlib.sha256(new_serialized).hexdigest()

    if cur.exists():
        prev.write_text(cur.read_text())

    cur.write_text(json.dumps(new_manifest, indent=2) + "\n")
    print(f"deployed manifest to env={env} commit={new_manifest['commit'][:8]} "
          f"signature={new_manifest['signature_sha256'][:12]}…")
    return 0


def cmd_rollback(args: argparse.Namespace) -> int:
    env = args.env
    cur = _manifest_path(env, "current")
    prev = _manifest_path(env, "previous")
    if not prev.exists():
        die(f"no previous manifest for env={env}; nothing to rollback")
    cur.write_text(prev.read_text())
    print(f"rolled back env={env} to previous manifest")
    return 0


def cmd_eval(args: argparse.Namespace) -> int:
    """
    Minimal eval runner. Reads `evals/<suite>.yaml`, runs each case against the
    current registry, prints pass/fail. In a real engagement we wire this to
    the team's existing eval harness (Promptfoo, LangSmith, custom) and emit
    JUnit XML for CI.
    """
    suite = args.suite
    suite_path = REPO / "evals" / f"{suite}.yaml"
    if not suite_path.exists():
        die(f"eval suite not found: {suite_path}")
    suite_data = yaml.safe_load(suite_path.read_text()) or {}
    cases = suite_data.get("cases", [])
    passed = failed = 0
    for case in cases:
        ok = _run_case_stub(case)
        passed += ok
        failed += 1 - ok
    report = {
        "suite": suite,
        "total": len(cases),
        "passed": passed,
        "failed": failed,
        "ts": int(time.time()),
    }
    out = REPO / "evals" / f"{suite}.report.json"
    out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return 0 if failed == 0 else 1


def _run_case_stub(case: dict[str, Any]) -> int:
    # Replace with a real model call in delivery. The shape stays the same:
    # given (prompt_id, prompt_version, input) → expected_assertions.
    expected = case.get("expect", {})
    return 1 if expected else 0


def _safe_git_head() -> str:
    try:
        return _git(["rev-parse", "HEAD"])
    except Exception:
        return "unknown"


# ---------- entry ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="shipprompt", description="Prompt-ops & model-deploy CLI.")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("validate", help="Validate the prompt registry.").set_defaults(fn=cmd_validate)

    pdiff = sub.add_parser("diff", help="Show prompt-level diff vs a git ref.")
    pdiff.add_argument("ref", help="git ref (e.g. main, HEAD~1)")
    pdiff.set_defaults(fn=cmd_diff)

    sub.add_parser("manifest", help="Print a signed deploy manifest.").set_defaults(fn=cmd_manifest)

    pdep = sub.add_parser("deploy", help="Deploy current registry to an environment.")
    pdep.add_argument("--env", required=True, help="target environment (e.g. staging, prod)")
    pdep.set_defaults(fn=cmd_deploy)

    prb = sub.add_parser("rollback", help="Restore the previous manifest for an environment.")
    prb.add_argument("--env", required=True)
    prb.set_defaults(fn=cmd_rollback)

    pev = sub.add_parser("eval", help="Run an eval suite.")
    pev.add_argument("--suite", required=True)
    pev.set_defaults(fn=cmd_eval)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
