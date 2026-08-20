#!/usr/bin/env python3
"""Validate the ClearGlass /data tree as one governed data fabric.

Hard failures:
- malformed JSON or CSV
- zero-byte governed data files
- unregistered or missing top-level data modules
- missing cataloged root datasets
- unsafe catalog paths

The script uses only the Python standard library so it can run locally and in
GitHub Actions without dependency installation.
"""
from __future__ import annotations

import csv
import io
import json
import sys
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CATALOG = DATA / "catalog.json"
TEXT_SUFFIXES = {".json", ".csv", ".md", ".txt"}
CATALOG_SCHEMA = "clearglass.data-fabric/v1"


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def safe_relative(value: str) -> bool:
    if not value or value.startswith("/"):
        return False
    path = PurePosixPath(value)
    return ".." not in path.parts


def validate_json(path: Path, errors: list[str]) -> object | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail(errors, f"invalid JSON: {path.relative_to(ROOT)}: {exc}")
        return None


def validate_csv(path: Path, errors: list[str]) -> None:
    try:
        text = path.read_text(encoding="utf-8-sig")
        list(csv.reader(io.StringIO(text), strict=True))
    except (UnicodeDecodeError, csv.Error) as exc:
        fail(errors, f"invalid CSV: {path.relative_to(ROOT)}: {exc}")


def load_catalog(errors: list[str]) -> dict:
    value = validate_json(CATALOG, errors)
    if not isinstance(value, dict):
        fail(errors, "catalog.json must contain a JSON object")
        return {}
    if value.get("schema") != CATALOG_SCHEMA:
        fail(errors, f"catalog schema must be {CATALOG_SCHEMA}")
    return value


def validate_catalog(catalog: dict, errors: list[str]) -> tuple[set[str], set[str]]:
    module_roots: set[str] = set()
    root_paths: set[str] = set()

    modules = catalog.get("modules")
    if not isinstance(modules, list):
        fail(errors, "catalog modules must be an array")
        modules = []

    seen_module_ids: set[str] = set()
    for item in modules:
        if not isinstance(item, dict):
            fail(errors, "every catalog module must be an object")
            continue
        module_id = item.get("id")
        root = item.get("root")
        if not isinstance(module_id, str) or not module_id:
            fail(errors, "catalog module is missing id")
        elif module_id in seen_module_ids:
            fail(errors, f"duplicate catalog module id: {module_id}")
        else:
            seen_module_ids.add(module_id)
        if not isinstance(root, str) or not safe_relative(root) or "/" in root:
            fail(errors, f"unsafe or invalid module root: {root!r}")
            continue
        module_roots.add(root)
        if not (DATA / root).is_dir():
            fail(errors, f"catalog module root does not exist: data/{root}")

    datasets = catalog.get("rootDatasets")
    if not isinstance(datasets, list):
        fail(errors, "catalog rootDatasets must be an array")
        datasets = []

    seen_dataset_ids: set[str] = set()
    for item in datasets:
        if not isinstance(item, dict):
            fail(errors, "every root dataset must be an object")
            continue
        dataset_id = item.get("id")
        relative = item.get("path")
        if not isinstance(dataset_id, str) or not dataset_id:
            fail(errors, "root dataset is missing id")
        elif dataset_id in seen_dataset_ids:
            fail(errors, f"duplicate root dataset id: {dataset_id}")
        else:
            seen_dataset_ids.add(dataset_id)
        if not isinstance(relative, str) or not safe_relative(relative) or "/" in relative:
            fail(errors, f"unsafe or invalid root dataset path: {relative!r}")
            continue
        root_paths.add(relative)
        if not (DATA / relative).is_file():
            fail(errors, f"catalog root dataset does not exist: data/{relative}")

    actual_modules = {path.name for path in DATA.iterdir() if path.is_dir()}
    for root in sorted(actual_modules - module_roots):
        fail(errors, f"unregistered data module: data/{root}")
    for root in sorted(module_roots - actual_modules):
        fail(errors, f"registered module missing from data tree: data/{root}")

    governed_root_files = {
        path.name
        for path in DATA.iterdir()
        if path.is_file() and path.suffix.lower() in {".json", ".csv"}
    }
    permitted_system_files = {"catalog.json"}
    for name in sorted(governed_root_files - root_paths - permitted_system_files):
        fail(errors, f"unregistered root dataset: data/{name}")

    return module_roots, root_paths


def validate_all_files(errors: list[str]) -> tuple[int, dict[str, int]]:
    counts = {"json": 0, "csv": 0, "text": 0, "other": 0}
    total = 0
    for path in sorted(DATA.rglob("*")):
        if not path.is_file():
            continue
        total += 1
        suffix = path.suffix.lower()
        if suffix in TEXT_SUFFIXES and path.stat().st_size == 0:
            fail(errors, f"zero-byte governed file: {path.relative_to(ROOT)}")
            continue
        if suffix == ".json":
            counts["json"] += 1
            validate_json(path, errors)
        elif suffix == ".csv":
            counts["csv"] += 1
            validate_csv(path, errors)
        elif suffix in {".md", ".txt"}:
            counts["text"] += 1
            try:
                path.read_text(encoding="utf-8")
            except UnicodeDecodeError as exc:
                fail(errors, f"invalid UTF-8 text: {path.relative_to(ROOT)}: {exc}")
        else:
            counts["other"] += 1
    return total, counts


def main() -> int:
    errors: list[str] = []
    if not DATA.is_dir():
        print("ERROR: data directory does not exist", file=sys.stderr)
        return 2
    if not CATALOG.is_file():
        print("ERROR: data/catalog.json does not exist", file=sys.stderr)
        return 2

    catalog = load_catalog(errors)
    modules, root_paths = validate_catalog(catalog, errors)
    total, counts = validate_all_files(errors)

    print(
        "ClearGlass Data Fabric: "
        f"files={total} modules={len(modules)} root_datasets={len(root_paths)} "
        f"json={counts['json']} csv={counts['csv']} text={counts['text']} other={counts['other']}"
    )

    if errors:
        print(f"FAILED: {len(errors)} integrity error(s)", file=sys.stderr)
        for message in errors:
            print(f" - {message}", file=sys.stderr)
        return 1

    print("PASS: every governed data asset is readable and every data module is cataloged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
