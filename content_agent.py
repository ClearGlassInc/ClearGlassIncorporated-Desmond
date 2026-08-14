#!/usr/bin/env python3
"""ClearGlass 50/30/20 content planning agent.

Produces drafts only. It never publishes content or performs network activity.
"""
from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

PILLARS = ("clarity_breakdown", "founder_reality", "product_demo")
ALLOCATION = (5, 3, 2)


@dataclass(frozen=True)
class Draft:
    number: int
    pillar: str
    title: str
    hook: str
    script: list[str]
    shot: str
    cta: str
    evidence: list[str]
    status: str = "DRAFT_REQUIRES_HUMAN_APPROVAL"


def _valid_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def validate_seed(seed: dict) -> None:
    required = {"opacity_issue", "security_consequence", "founder_truth", "product", "feature", "pain", "demo", "sources"}
    missing = sorted(required - seed.keys())
    if missing:
        raise ValueError("Missing seed fields: " + ", ".join(missing))
    if not isinstance(seed["sources"], list) or not seed["sources"]:
        raise ValueError("At least one public source is required for Clarity Breakdowns")
    if any(not _valid_url(item) for item in seed["sources"]):
        raise ValueError("Every source must be a valid HTTPS URL")
    for key in required - {"sources"}:
        if not isinstance(seed[key], str) or not seed[key].strip():
            raise ValueError(f"{key} must be a non-empty string")


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_plan(seed: dict) -> list[Draft]:
    validate_seed(seed)
    s = {key: [_clean(x) for x in value] if key == "sources" else _clean(value) for key, value in seed.items()}
    drafts: list[Draft] = []
    for index in range(ALLOCATION[0]):
        drafts.append(Draft(
            len(drafts) + 1, PILLARS[0], f"Clarity Breakdown {index + 1}",
            f"If the public cannot see {s['opacity_issue']}, defenders cannot measure the risk.",
            [f"Public problem: {s['opacity_issue']}.", f"Security consequence: {s['security_consequence']}.",
             "Show the primary-source evidence on screen. Separate verified fact from analysis.",
             "Close: transparency is a security control, not decoration."],
            "Direct-to-camera; insert source screenshot and highlight the exact supporting line.",
            "Ask one precise accountability question.", s["sources"]))
    for index in range(ALLOCATION[1]):
        drafts.append(Draft(
            len(drafts) + 1, PILLARS[1], f"Founder Reality {index + 1}",
            "Building security infrastructure is less glamorous than the finished dashboard.",
            [s["founder_truth"], "Name the decision, constraint, or mistake plainly.",
             "State what changed today and what ships next."],
            "Raw phone video at desk, parked car, or walking; one take; natural sound; no beauty filter.",
            "Invite operators to compare notes.", []))
    for index in range(ALLOCATION[2]):
        drafts.append(Draft(
            len(drafts) + 1, PILLARS[2], f"{s['product']} in 30 Seconds {index + 1}",
            f"Still fighting {s['pain']}?",
            [f"Pain (0-7s): {s['pain']}.", f"Feature (7-15s): {s['feature']}.",
             f"Demo (15-25s): {s['demo']}.", "Close (25-30s): show the measurable operator outcome; do not invent results."],
            "Screen recording with cursor emphasis, large captions, and a visible 30-second timer.",
            f"Request a {s['product']} walkthrough.", []))
    return drafts


def render_markdown(drafts: list[Draft], generated: str) -> str:
    lines = ["# ClearGlass Content Brief", "", f"Generated: {generated}", "", "Allocation: 5 Clarity Breakdowns / 3 Founder Reality / 2 Product Demos", "",
             "> Drafts only. Verify every factual claim against the linked primary source. Human approval is mandatory before publication.", ""]
    for item in drafts:
        lines += [f"## {item.number}. {item.title}", "", f"**Pillar:** `{item.pillar}`  ", f"**Status:** `{item.status}`  ",
                  f"**Hook:** {item.hook}", "", "**Script**", ""]
        lines += [f"{i}. {line}" for i, line in enumerate(item.script, 1)]
        lines += ["", f"**Shot:** {item.shot}", "", f"**CTA:** {item.cta}", ""]
        if item.evidence:
            lines += ["**Evidence**", ""] + [f"- {url}" for url in item.evidence] + [""]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate a governed ClearGlass 50/30/20 content brief")
    parser.add_argument("--seed", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("content-brief.md"))
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args()
    seed = json.loads(args.seed.read_text(encoding="utf-8"))
    drafts = build_plan(seed)
    args.output.write_text(render_markdown(drafts, date.today().isoformat()) + "\n", encoding="utf-8")
    if args.json_output:
        args.json_output.write_text(json.dumps([asdict(item) for item in drafts], indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
