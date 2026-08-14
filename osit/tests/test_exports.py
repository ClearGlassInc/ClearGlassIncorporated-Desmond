import json

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd

from osit.provenance import ProvenanceManifest, register_artifact, write_manifest
from osit.visualization import export_geopackage, export_graphml, export_metric_table


def sample_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.graph["crs"] = "EPSG:4326"
    graph.add_node(1, x=-79.80, y=43.30)
    graph.add_node(2, x=-79.79, y=43.31)
    graph.add_edge(1, 2, length=100.0)
    return graph


def test_csv_and_parquet_exports_round_trip(tmp_path) -> None:
    table = pd.DataFrame([{"node": 1, "betweenness": 0.5}])
    csv_path = export_metric_table(table, tmp_path / "metrics.csv")
    parquet_path = export_metric_table(table, tmp_path / "metrics.parquet")
    assert pd.read_csv(csv_path).iloc[0]["betweenness"] == 0.5
    assert pd.read_parquet(parquet_path).iloc[0]["betweenness"] == 0.5


def test_graphml_export_round_trip(tmp_path) -> None:
    paths = export_graphml({"walk": sample_graph()}, tmp_path / "graphs")
    loaded = ox.load_graphml(paths[0])
    assert loaded.number_of_nodes() == 2
    assert loaded.number_of_edges() == 1


def test_geopackage_exports_all_mode_layers(tmp_path) -> None:
    output = export_geopackage(
        {"walk": sample_graph(), "bike": sample_graph()},
        tmp_path / "osit.gpkg",
    )
    layers = set(gpd.list_layers(output)["name"])
    expected = {"walk_nodes", "walk_edges", "bike_nodes", "bike_edges"}
    assert expected <= layers
    for layer in expected:
        assert not gpd.read_file(output, layer=layer).empty


def test_manifest_records_artifact_checksum(tmp_path) -> None:
    artifact_path = tmp_path / "artifact.txt"
    artifact_path.write_text("OSIT", encoding="utf-8")
    artifact = register_artifact(artifact_path, "text/plain")
    manifest = ProvenanceManifest(project_name="test", artifacts=[artifact])
    output = write_manifest(manifest, tmp_path / "manifest.json")
    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["label"].startswith("OSIT")
    assert len(data["artifacts"][0]["sha256"]) == 64
