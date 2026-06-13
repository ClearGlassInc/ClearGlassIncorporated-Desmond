#!/usr/bin/env python3
# Copyright (c) 2024-2026 ClearGlass Inc. All Rights Reserved.
# Proprietary and confidential. See LICENSE for terms.
"""Detect people in an input image.

CLI entry point that accepts an image path via a parameter and runs people
detection over it, emitting the result to stdout (human-readable or JSON).

Run locally:
  python detect_people.py path/to/image.jpg
  python detect_people.py path/to/image.jpg --json
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SUPPORTED_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}


def detect_people(image_path: Path) -> list[dict[str, float]]:
    """Return bounding boxes for people detected in ``image_path``.

    Each detection is a dict with ``x``, ``y``, ``width``, ``height`` and
    ``confidence`` keys. The detection backend is pluggable; until a model is
    wired in this returns an empty list rather than fabricating detections.

    Raises:
        FileNotFoundError: if ``image_path`` does not point to a file.
        ValueError: if the file extension is not a supported image type.
    """
    if not image_path.is_file():
        raise FileNotFoundError(f"Image not found: {image_path}")
    if image_path.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(f"Unsupported image type: {image_path.suffix or '<none>'}")
    # Detection backend not yet configured; report no detections.
    return []


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line argument parser."""
    parser = argparse.ArgumentParser(description="Detect people in an image.")
    parser.add_argument("image", type=Path, help="Path to the input image.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit results as JSON instead of human-readable text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the detector against the image given on the command line."""
    args = build_parser().parse_args(argv)
    try:
        people = detect_people(args.image)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"image": str(args.image), "count": len(people), "people": people}))
    else:
        print(f"Detected {len(people)} person(s) in {args.image}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
