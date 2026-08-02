#!/usr/bin/env python3
"""Regenerate the site's browser-tab / install icon set from one source image.

Every indexable page links its tab icon to ``/logo.png`` (see the
"Browser Tab Icons" block in each ``<head>``), and the PWA manifests point at
``/icon-192.png`` and ``/icon-512.png``. This script derives that whole family
from a single square-cropped source so the tab, the iOS home screen, and the
installed PWA never drift apart.

Note the site's *visible* logo is ``assets/images/clearglass-logo.png`` — a
different asset. This script deliberately does not touch it.

Usage::

    python3 tools/generate_favicons.py --source path/to/source.png
    python3 tools/generate_favicons.py --source src.png --dry-run

Requires Pillow (``pip install Pillow``); everything else is stdlib.
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover - dependency guard
    sys.exit("Pillow is required: pip install Pillow")

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# (filename, edge length in px). logo.png is the master the <link rel="icon">
# tags resolve to; the rest are size-specific derivatives.
PNG_TARGETS: list[tuple[str, int]] = [
    ("logo.png", 1024),
    ("icon-512.png", 512),
    ("icon-192.png", 192),
    ("apple-touch-icon.png", 180),
    ("favicon-32.png", 32),
    ("favicon-16.png", 16),
]

# Windows tiles and legacy browsers read the multi-resolution .ico.
ICO_NAME = "favicon.ico"
ICO_SIZES = [(16, 16), (32, 32), (48, 48)]

MANIFEST = "site.webmanifest"


def square_crop(img: Image.Image) -> Image.Image:
    """Center-crop to a square so no resize distorts the artwork."""
    width, height = img.size
    if width == height:
        return img
    edge = min(width, height)
    left = (width - edge) // 2
    top = (height - edge) // 2
    return img.crop((left, top, left + edge, top + edge))


def load_source(path: pathlib.Path) -> Image.Image:
    img = Image.open(path)
    # Flatten alpha onto white so tabs never render a black halo, then drop to
    # RGB to match the existing icon assets.
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        flat = Image.new("RGBA", img.size, (255, 255, 255, 255))
        flat.alpha_composite(img)
        img = flat
    return square_crop(img.convert("RGB"))


def sync_manifest(edge: int, dry_run: bool) -> None:
    """Keep site.webmanifest's declared logo.png size honest."""
    path = REPO_ROOT / MANIFEST
    if not path.exists():
        return
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = False
    for icon in data.get("icons", []):
        if icon.get("src", "").lstrip("/") == "logo.png":
            want = f"{edge}x{edge}"
            if icon.get("sizes") != want:
                icon["sizes"] = want
                changed = True
    if not changed:
        return
    print(f"  {MANIFEST} -> logo.png sizes {edge}x{edge}")
    if not dry_run:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        required=True,
        help="Path to the source image (square or better; it is center-cropped).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report what would be written without touching any file.",
    )
    args = parser.parse_args()

    source = pathlib.Path(args.source)
    if not source.is_absolute():
        source = (REPO_ROOT / source).resolve()
    if not source.exists():
        print(f"source image not found: {source}", file=sys.stderr)
        return 1

    img = load_source(source)
    print(f"source {source.name}: cropped to {img.size[0]}x{img.size[1]}")

    for name, edge in PNG_TARGETS:
        out = REPO_ROOT / name
        print(f"  {name} -> {edge}x{edge}")
        if not args.dry_run:
            img.resize((edge, edge), Image.LANCZOS).save(out, "PNG", optimize=True)

    ico = REPO_ROOT / ICO_NAME
    print(f"  {ICO_NAME} -> {', '.join(f'{w}x{h}' for w, h in ICO_SIZES)}")
    if not args.dry_run:
        img.resize((48, 48), Image.LANCZOS).save(ico, "ICO", sizes=ICO_SIZES)

    sync_manifest(PNG_TARGETS[0][1], args.dry_run)

    if args.dry_run:
        print("dry run: nothing written")
    else:
        print("done — bump VERSION in sw.js so cached tabs pick up the new icon")
    return 0


if __name__ == "__main__":
    sys.exit(main())
