from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd

LABEL = "OSIT — Open-Source Infrastructure Topology Intelligence"


def export_graphml(graphs: dict[str, nx.MultiDiGraph], directory: str | Path) -> list[Path]:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    outputs: list[Path] = []
    for mode, graph in graphs.items():
        path = root / f"{mode}.graphml"
        ox.io.save_graphml(graph, filepath=path)
        outputs.append(path)
    return outputs


def export_geopackage(graphs: dict[str, nx.MultiDiGraph], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    first_layer = True
    for mode, graph in graphs.items():
        nodes, edges = ox.graph_to_gdfs(graph)
        nodes.to_file(
            output,
            layer=f"{mode}_nodes",
            driver="GPKG",
            mode="w" if first_layer else "a",
        )
        first_layer = False
        edges.to_file(output, layer=f"{mode}_edges", driver="GPKG", mode="a")
    return output


def export_geojson_edges(graph: nx.MultiDiGraph, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    _, edges = ox.graph_to_gdfs(graph)
    edges.to_file(output, driver="GeoJSON")
    return output


def export_metric_table(table: pd.DataFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.suffix.lower() == ".parquet":
        table.to_parquet(output, index=False)
    elif output.suffix.lower() == ".csv":
        table.to_csv(output, index=False)
    else:
        raise ValueError("metric table must use .csv or .parquet")
    return output


def write_executive_brief(summary: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# {LABEL}",
        "",
        "## Scope",
        f"- Project: {summary.get('project_name', '')}",
        f"- Area of interest: {summary.get('area_of_interest', '')}",
        f"- Analysis date: {summary.get('analysis_date_utc', '')}",
        "",
        "## Verified Network Metrics",
    ]
    for mode, metrics in summary.get("network_metrics", {}).items():
        lines.append(f"### {mode}")
        for key, value in metrics.items():
            lines.append(f"- {key}: {value}")
    lines.extend(
        [
            "",
            "## Model-Derived Findings",
            "- Topology flags are graph-model outputs, not claims of real-world operational criticality.",
            "",
            "## Limitations",
            "- OpenStreetMap completeness and currency vary by feature and geography.",
            "- Travel times derived from tags/default speeds are estimates unless a verified public operational feed is used.",
            "- Field validation is required before consequential planning decisions.",
        ]
    )
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


def write_html_report(summary: dict[str, Any], path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    payload = html.escape(json.dumps(summary, indent=2, default=str))
    document = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{LABEL}</title><style>body{{font-family:system-ui;max-width:1100px;margin:2rem auto;padding:0 1rem;line-height:1.5}}pre{{overflow:auto;background:#111;color:#eee;padding:1rem}}.caveat{{border-left:4px solid #b36b00;padding-left:1rem}}</style></head>
<body><h1>{LABEL}</h1><p class="caveat">Planning/research output. Graph-centrality and topology flags do not establish real-world operational criticality.</p><pre>{payload}</pre></body></html>"""
    output.write_text(document, encoding="utf-8")
    return output


def write_geojson(geodata: gpd.GeoDataFrame, path: str | Path) -> Path:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    geodata.to_file(output, driver="GeoJSON")
    return output
