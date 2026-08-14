from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

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
    output.write_text(
        json.dumps(manifest.model_dump(mode="json"), indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return output
