from __future__ import annotations

import hashlib
import json
import platform
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
import shapely
from pydantic import BaseModel, Field


class SourceRecord(BaseModel):
    source_name: str
    source_url: str
    license: str
    retrieved_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    query_parameters: dict[str, Any] = Field(default_factory=dict)
    geographic_coverage: str = ""
    coordinate_reference_system: str = "EPSG:4326"
    data_quality_notes: str = ""
    dataset_sha256: str | None = None
    node_count: int | None = None
    edge_count: int | None = None
    feature_count: int | None = None
    notes: list[str] = Field(default_factory=list)


class ArtifactRecord(BaseModel):
    path: str
    sha256: str
    bytes: int
    media_type: str | None = None


class ProvenanceManifest(BaseModel):
    label: str = "OSIT — Open-Source Infrastructure Topology Intelligence"
    generated_at_utc: datetime = Field(default_factory=lambda: datetime.now(UTC))
    project_name: str
    sources: list[SourceRecord] = Field(default_factory=list)
    artifacts: list[ArtifactRecord] = Field(default_factory=list)
    processing: list[dict[str, Any]] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime: dict[str, Any] = Field(
        default_factory=lambda: {
            "python": platform.python_version(),
            "osmnx": ox.__version__,
            "shapely": shapely.__version__,
            "networkx": nx.__version__,
        }
    )
    manifest_sha256: str | None = None


def _canonical_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, dict):
        return {str(k): _canonical_value(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple)):
        return [_canonical_value(v) for v in value]
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    return str(value)


def canonical_sha256(gdf: gpd.GeoDataFrame) -> str:
    """Hash WKB + canonical attributes + source index, independent of row/column order."""
    frame = gdf.copy()
    geometry_column = frame.geometry.name
    frame["_geometry_wkb_hex"] = frame.geometry.to_wkb(hex=True)
    frame["_source_index"] = [
        json.dumps(_canonical_value(index), sort_keys=True, separators=(",", ":"))
        for index in frame.index
    ]
    frame = frame.drop(columns=[geometry_column], errors="ignore")
    columns = sorted(frame.columns)

    records: list[str] = []
    for row in frame[columns].itertuples(index=False, name=None):
        canonical = {
            column: _canonical_value(value)
            for column, value in zip(columns, row, strict=True)
        }
        records.append(json.dumps(canonical, sort_keys=True, separators=(",", ":")))

    payload = "\n".join(sorted(records)) + ("\n" if records else "")
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def register_artifact(path: str | Path, media_type: str | None = None) -> ArtifactRecord:
    artifact_path = Path(path)
    return ArtifactRecord(
        path=artifact_path.as_posix(),
        sha256=sha256_file(artifact_path),
        bytes=artifact_path.stat().st_size,
        media_type=media_type,
    )


def write_manifest(manifest: ProvenanceManifest, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = manifest.model_dump(mode="json")
    payload["manifest_sha256"] = None
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    payload["manifest_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    output.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return output
