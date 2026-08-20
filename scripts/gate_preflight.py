#!/usr/bin/env python3
"""Run the repository's CI gates locally, without GitHub-hosted runners.

Why this exists
---------------
When the GitHub account is billing-locked, runner admission fails *before* any
job step executes (see `docs/ACTIONS_BILLING_FALLBACK.md`). Workflows still
appear in the Actions tab, but they report zero executed steps — so merges keep
landing on `main` with no gate ever having run against them.

That is not a theoretical risk. During the 2026-08-14 lock, five gates went red
on `main` and stayed red for days: root pytest aborted at collection (0 of 1,890
tests ran), ruff failed, the internal-link and design-system contracts failed for
an unregistered page, and the provenance manifest drifted. Every one of them is
reproducible on a laptop in under two minutes. Nothing about them needed a hosted
runner — only something that actually ran them.

This script is that something. It runs the runner-independent gates and prints a
verdict, so a change can be verified before merge while Actions is unavailable.

Honesty rules
-------------
- A gate whose tool is missing is reported SKIP, never PASS. A skipped gate is
  not a verified gate, and the summary says so.
- This does not reproduce the hosted-runner-only jobs (Node tooling, Lighthouse,
  browser suites, deploy). Those stay unverified until runners return, and the
  summary lists them by name rather than quietly omitting them.
- Passing here is not the same as CI-verified. It is evidence, not a substitute.

Usage
-----
    python3 scripts/gate_preflight.py              # all gates
    python3 scripts/gate_preflight.py --no-generate  # skip gates that rewrite files

Exit status is 0 only when every executed gate passed. Standard library only, so
it runs in the same minimal environments the governance modules target.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PASS, FAIL, SKIP = "PASS", "FAIL", "SKIP"

# Jobs that genuinely cannot run here. Named so the summary can admit the gap
# instead of implying full coverage.
RUNNER_ONLY_JOBS = (
    "Node Tooling (npm ci / typecheck / next build)",
    "Lighthouse budgets",
    "Playwright browser suites",
    "Commerce Deploy render hook + Pages deployment",
)


class Gate:
    """One locally runnable CI gate."""

    def __init__(
        self,
        name: str,
        argv: list[str],
        *,
        requires: str | None = None,
        mutates: bool = False,
        remedy: str = "",
    ) -> None:
        self.name = name
        self.argv = argv
        self.requires = requires
        self.mutates = mutates
        self.remedy = remedy
        self.status = SKIP
        self.detail = ""
        self.seconds = 0.0

    def run(self) -> None:
        if self.requires and shutil.which(self.requires) is None:
            self.detail = f"{self.requires} not installed — gate not verified"
            return
        started = time.monotonic()
        try:
            proc = subprocess.run(
                self.argv, cwd=ROOT, capture_output=True, text=True, timeout=2400
            )
        except FileNotFoundError:
            self.detail = f"{self.argv[0]} not found — gate not verified"
            return
        except subprocess.TimeoutExpired:
            self.status, self.detail = FAIL, "timed out after 2400s"
            self.seconds = time.monotonic() - started
            return
        self.seconds = time.monotonic() - started
        self.status = PASS if proc.returncode == 0 else FAIL
        if self.status == FAIL:
            tail = (proc.stdout or "").strip().splitlines()[-12:]
            err = (proc.stderr or "").strip().splitlines()[-6:]
            self.detail = "\n".join(["    " + ln for ln in tail + err])


def build_gates(include_generators: bool) -> list[Gate]:
    py = sys.executable
    gates = [
        Gate(
            "Lint (ruff)",
            ["ruff", "check", "."],
            requires="ruff",
            remedy="ruff check . --fix",
        ),
        Gate(
            "Root suite collection integrity",
            [py, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider"],
            remedy="guard commerce-only imports with pytest.importorskip",
        ),
        Gate(
            "Python tests (root testpaths)",
            [py, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
            remedy="python -m pytest -q",
        ),
        Gate(
            "Internal links current",
            [py, "tools/internal_links.py", "--check"],
            remedy="python3 tools/internal_links.py",
        ),
        Gate(
            "Design system contracts",
            [py, "tools/design_system.py", "--check"],
            remedy="python3 tools/design_system.py",
        ),
        Gate(
            "SEO audit",
            [py, "tools/seo_audit.py"],
            remedy="address the reported errors",
        ),
        Gate(
            "Site reliability audit",
            [py, "scripts/site_reliability_audit.py"],
            remedy="address the reported errors",
        ),
    ]
    if include_generators:
        gates += [
            Gate(
                "Search assets current",
                [py, "tools/generate_search_assets.py"],
                mutates=True,
                remedy="commit the regenerated sitemap.xml / feed.xml / page-intents.json",
            ),
            Gate(
                "Provenance manifest current",
                [py, "tools/security_release_manifest.py"],
                mutates=True,
                remedy="commit the regenerated provenance/release-manifest.json",
            ),
        ]
    return gates


def derived_file_drift() -> list[str]:
    """Files a generator rewrote that are not yet committed."""
    proc = subprocess.run(
        ["git", "diff", "--name-only"], cwd=ROOT, capture_output=True, text=True
    )
    if proc.returncode != 0:
        return []
    return [ln for ln in proc.stdout.split("\n") if ln.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-generate",
        action="store_true",
        help="skip gates that regenerate derived files in the working tree",
    )
    args = parser.parse_args()

    gates = build_gates(include_generators=not args.no_generate)
    before = set(derived_file_drift())

    print("== ClearGlass gate preflight (Actions-independent) ==")
    print(f"Repository: {ROOT}\n")

    for gate in gates:
        print(f"-- {gate.name} ...", flush=True)
        gate.run()
        print(f"   {gate.status} ({gate.seconds:.1f}s)")
        if gate.detail:
            print(gate.detail)

    failed = [g for g in gates if g.status == FAIL]
    skipped = [g for g in gates if g.status == SKIP]
    passed = [g for g in gates if g.status == PASS]

    print("\n== Summary ==")
    for gate in gates:
        print(f"  {gate.status:4}  {gate.name}")
    print(f"\n{len(passed)} passed | {len(failed)} failed | {len(skipped)} skipped")

    new_drift = sorted(set(derived_file_drift()) - before)
    if new_drift:
        print("\nGenerators rewrote these files — commit them:")
        for path in new_drift:
            print(f"  {path}")

    if failed:
        print("\nRemedies:")
        for gate in failed:
            if gate.remedy:
                print(f"  {gate.name}: {gate.remedy}")

    if skipped:
        print("\nNot verified (tooling missing):")
        for gate in skipped:
            print(f"  {gate.name}: {gate.detail}")

    print("\nStill unverified — requires GitHub-hosted runners:")
    for job in RUNNER_ONLY_JOBS:
        print(f"  {job}")
    print(
        "\nA green preflight is evidence, not a CI-verified release. Do not "
        "describe a build as CI-verified until the blocked Actions jobs have "
        "actually executed and passed."
    )

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
