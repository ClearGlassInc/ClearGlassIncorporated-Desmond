import json

import pandas as pd

from osit.provenance import ProvenanceManifest, register_artifact, write_manifest
from osit.visualization import export_metric_table


def test_csv_and_parquet_exports_round_trip(tmp_path) -> None:
    table = pd.DataFrame([{"node": 1, "betweenness": 0.5}])
    csv_path = export_metric_table(table, tmp_path / "metrics.csv")
    parquet_path = export_metric_table(table, tmp_path / "metrics.parquet")
    assert pd.read_csv(csv_path).iloc[0]["betweenness"] == 0.5
    assert pd.read_parquet(parquet_path).iloc[0]["betweenness"] == 0.5


def test_manifest_records_artifact_checksum(tmp_path) -> None:
    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text("OSIT", encoding="utf-8")
    artifact = register_artifact(artifact_path, "text/plain")
    manifest = ProvenanceManifest(project_name="test", artifacts=[artifact])
    output = write_manifest(manifest, tmp_path / "manifest.json")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["label"].startswith("OSIT")
    assert len(data["artifacts"][0]["sha256"]) == 64
