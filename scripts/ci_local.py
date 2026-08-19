#!/usr/bin/env python3
"""Run the CI workflow's gates on this machine.

`.github/workflows/ci.yml` is the contract every change is supposed to satisfy,
but it only runs when GitHub can start a hosted runner. When it cannot — an
Actions spending limit, a billing lock, a hosted-runner incident — the checks go
red in seconds without executing a step, and a merge lands with no signal at
all. That is how a truncated homepage, an unparseable sitemap and a repo-wide
test-collection failure each reached `main`.

This runner executes the same commands those jobs run, in the same order, on
whatever machine you are sitting at:

    python3 scripts/ci_local.py              # every gate
    python3 scripts/ci_local.py --fast       # skip the network/build-heavy ones
    python3 scripts/ci_local.py --list       # show the gate set
    python3 scripts/ci_local.py --only lint python-tests

Exit status is 0 only when every selected gate passed, so it composes into a
pre-push hook or a release checklist.

`tests/test_ci_local.py` asserts this file covers every job in ci.yml. A local
gate runner that silently omits a gate is worse than no runner at all, because
it produces a green summary that nobody can act on.

stdlib only, so it runs before any dependency is installed.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

PY = sys.executable or "python3"

# Capability tags. A gate is skipped (not failed) when its requirement is
# unavailable, and the summary says so rather than implying the gate passed.
# Reporting FAIL for a gate that never ran is the same lie in the other
# direction: it looks like a defect in the code under test.
NEEDS_NODE = "node"
NEEDS_NETWORK = "network"
NEEDS_CHROME = "chrome"
NEEDS_CLEAN_TREE = "clean-tree"
NEEDS_COMMERCE_STACK = "commerce-stack"

# Files whose committed contents the search-integrity gate compares against a
# fresh generator run. Local edits to them make that comparison meaningless.
GENERATED_ASSETS = ("sitemap.xml", "feed.xml", "data/seo/page-intents.json")


@dataclass(frozen=True)
class Gate:
    """One CI job, expressed as the commands that job actually runs."""

    key: str
    """Selector used by --only/--skip."""

    job: str
    """The `jobs.<id>` key in ci.yml this mirrors. Kept in sync by a test."""

    summary: str
    steps: tuple[tuple[str, ...], ...]
    requires: frozenset[str] = field(default_factory=frozenset)


GATES: tuple[Gate, ...] = (
    Gate(
        key="lint",
        job="lint",
        summary="ruff over the whole repository",
        steps=((PY, "-m", "ruff", "check", "."),),
    ),
    Gate(
        key="python-tests",
        job="python-tests",
        summary="the configured pytest suite (all four testpaths)",
        # No path argument, exactly as ci.yml runs it. pyproject.toml's
        # testpaths cover artemis/tests, tests, sentinel/tests and the commerce
        # control-plane tests. This gate used to run `pytest tests/`, which
        # collects 1339 of 2027 tests — it reported PASS while the commerce
        # governance and route-auth suites, the ones CLAUDE.md calls
        # load-bearing, had not been run at all.
        steps=((PY, "-m", "pytest", "-q"),),
        requires=frozenset({NEEDS_COMMERCE_STACK}),
    ),
    Gate(
        key="site-audit",
        job="site-audit",
        summary="link, metadata and asset reachability audit",
        steps=((PY, "scripts/site_reliability_audit.py"),),
    ),
    Gate(
        key="search-integrity",
        job="search-integrity",
        summary="generated search assets are current, indexable and linked",
        steps=(
            (PY, "tools/generate_search_assets.py"),
            # The generator is idempotent; a diff here means the committed
            # sitemap/feed/intent-map are stale against the pages on disk.
            ("git", "diff", "--exit-code", "--", "sitemap.xml", "feed.xml", "data/seo/page-intents.json"),
            (PY, "tools/seo_audit.py"),
            (PY, "tools/internal_links.py", "--check"),
        ),
        requires=frozenset({NEEDS_CLEAN_TREE}),
    ),
    Gate(
        key="workflow-doctor",
        job="workflow-doctor",
        summary="workflow syntax and supply-chain safety invariants",
        steps=(
            (PY, "scripts/workflow_doctor.py"),
            (PY, "scripts/audit_github_actions.py"),
        ),
    ),
    Gate(
        key="osint-deck",
        job="osint-deck",
        summary="OSINT deck release gate",
        steps=((PY, "scripts/osint_deck_release.py", "--strict"),),
    ),
    Gate(
        key="node-tooling",
        job="node-tooling",
        summary="TypeScript typecheck, unit tests and deterministic build",
        steps=(
            ("npm", "ci"),
            ("npm", "run", "typecheck"),
            ("npm", "test"),
            ("npm", "run", "build"),
        ),
        requires=frozenset({NEEDS_NODE, NEEDS_NETWORK}),
    ),
    Gate(
        key="lighthouse",
        job="lighthouse",
        summary="performance, accessibility and SEO budgets",
        steps=(("npx", "--yes", "@lhci/cli@0.15.1", "autorun", "--config=lighthouserc.json"),),
        requires=frozenset({NEEDS_NODE, NEEDS_NETWORK, NEEDS_CHROME}),
    ),
)

FAST_SKIP = frozenset({NEEDS_NETWORK})


def dirty_generated_assets() -> list[str]:
    """Generated assets with uncommitted local edits."""
    completed = subprocess.run(
        ["git", "status", "--porcelain", "--", *GENERATED_ASSETS],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    return [line[3:] for line in completed.stdout.splitlines() if line.strip()]


def commerce_stack_available() -> bool:
    """Whether the commerce control-plane tests can be collected at all.

    Without these, pytest errors during collection of
    clearglass-commerce/control-plane/tests — which reads as a defect in the
    code rather than a missing dependency.
    """
    return all(importlib.util.find_spec(name) for name in ("fastapi", "sqlalchemy", "httpx"))


def chrome_available() -> bool:
    if any(shutil.which(name) for name in ("google-chrome", "chromium", "chromium-browser")):
        return True
    # Lighthouse also accepts an explicit binary path.
    return bool(os.environ.get("CHROME_PATH"))


def missing_requirements(gate: Gate, *, fast: bool) -> list[str]:
    """Why this gate cannot run here, or an empty list when it can."""
    missing: list[str] = []
    if NEEDS_NODE in gate.requires and shutil.which("npm") is None:
        missing.append("npm not installed")
    if NEEDS_CHROME in gate.requires and not chrome_available():
        missing.append("no Chrome/Chromium found (set CHROME_PATH)")
    if NEEDS_COMMERCE_STACK in gate.requires and not commerce_stack_available():
        missing.append(
            "commerce control-plane deps missing — "
            "pip install -r clearglass-commerce/control-plane/requirements.txt"
        )
    if NEEDS_CLEAN_TREE in gate.requires:
        # This gate asks whether the *committed* assets match a fresh generator
        # run. With local edits in flight the comparison answers a different
        # question, and failing on it would just be reporting your own work.
        dirty = dirty_generated_assets()
        if dirty:
            missing.append("uncommitted changes in " + ", ".join(dirty) + " — commit, then re-run")
    if fast and gate.requires & FAST_SKIP:
        missing.append("--fast")
    return missing


def run_gate(gate: Gate) -> tuple[bool, str]:
    """Run every step; stop at the first failure and return its output."""
    for step in gate.steps:
        completed = subprocess.run(
            step, cwd=ROOT, capture_output=True, text=True, check=False
        )
        if completed.returncode != 0:
            rendered = " ".join(step)
            output = (completed.stdout or "") + (completed.stderr or "")
            return False, f"$ {rendered}\n{output.strip()}"
    return True, ""


HOOK = """#!/bin/sh
# Installed by scripts/ci_local.py --install-hook.
# Runs the fast gate set before a push. Bypass a known-good push with
# `git push --no-verify`.
exec python3 scripts/ci_local.py --fast
"""


def install_hook() -> int:
    """Install a pre-push hook that runs the fast gates."""
    hooks = ROOT / ".git" / "hooks"
    if not hooks.is_dir():
        print(f"no hooks directory at {hooks}", file=sys.stderr)
        return 1
    path = hooks / "pre-push"
    if path.exists() and "ci_local.py" not in path.read_text(encoding="utf-8"):
        print(f"refusing to overwrite an existing hook: {path}", file=sys.stderr)
        return 1
    path.write_text(HOOK, encoding="utf-8")
    path.chmod(0o755)
    print(f"installed {path} — bypass one push with `git push --no-verify`")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--list", action="store_true", help="print the gate set and exit")
    parser.add_argument(
        "--install-hook",
        action="store_true",
        help="install a pre-push git hook that runs the fast gates",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="skip gates that need the network (node-tooling, lighthouse)",
    )
    parser.add_argument("--only", nargs="+", metavar="GATE", help="run just these gates")
    parser.add_argument("--skip", nargs="+", metavar="GATE", help="run everything but these")
    return parser.parse_args(argv)


def select(args: argparse.Namespace) -> list[Gate]:
    keys = {gate.key for gate in GATES}
    for name in (*(args.only or ()), *(args.skip or ())):
        if name not in keys:
            raise SystemExit(f"unknown gate {name!r}; choose from {', '.join(sorted(keys))}")
    chosen = [g for g in GATES if not args.only or g.key in args.only]
    return [g for g in chosen if not args.skip or g.key not in args.skip]


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    if args.install_hook:
        return install_hook()

    if args.list:
        for gate in GATES:
            tags = f"  [{', '.join(sorted(gate.requires))}]" if gate.requires else ""
            print(f"{gate.key:18} {gate.summary}{tags}")
        return 0

    gates = select(args)
    results: list[tuple[str, str, float, str]] = []
    failures = 0

    for gate in gates:
        skip_reasons = missing_requirements(gate, fast=args.fast)
        if skip_reasons:
            results.append((gate.key, "SKIP", 0.0, "; ".join(skip_reasons)))
            continue

        print(f"… {gate.key}", flush=True)
        started = time.monotonic()
        passed, output = run_gate(gate)
        elapsed = time.monotonic() - started
        results.append((gate.key, "PASS" if passed else "FAIL", elapsed, output))
        if not passed:
            failures += 1

    print("\n== CI gates (local) ==")
    skipped = 0
    for key, status, elapsed, detail in results:
        timing = f"{elapsed:6.1f}s" if status != "SKIP" else "      -"
        print(f"  {status:4}  {timing}  {key}")
        if status == "SKIP":
            skipped += 1
            print(f"          not run: {detail}")

    for key, status, _elapsed, detail in results:
        if status == "FAIL":
            print(f"\n--- {key} ---\n{detail}")

    passed_count = sum(1 for _, status, _, _ in results if status == "PASS")
    print(f"\n{passed_count} passed, {failures} failed, {skipped} skipped")

    if skipped:
        print("Skipped gates were not verified — do not read this as a green run.")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
