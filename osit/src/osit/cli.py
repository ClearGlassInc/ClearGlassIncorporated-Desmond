from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import structlog
import typer

from .acquisition import collect
from .config import load_config
from .metrics import centrality_table, topology_summary
from .multimodal import normalized_multimodal_graph
from .network_builder import graph_quality, prepare_graph
from .provenance import ProvenanceManifest, register_artifact, write_manifest
from .resilience import topology_flags
from .validation import validate_aoi
from .visualization import (
    export_geopackage,
    export_graphml,
    export_metric_table,
    write_executive_brief,
    write_html_report,
)

app = typer.Typer(help="OSIT — Open-Source Infrastructure Topology Intelligence")
log = structlog.get_logger("osit")


def _configure_logging() -> None:
    structlog.configure(processors=[structlog.processors.TimeStamper(fmt="iso"), structlog.processors.JSONRenderer()])


@app.command()
def validate(config: Path = typer.Option(Path("config/analysis.yaml"), exists=True)) -> None:
    """Validate deterministic configuration and non-place AOI geometry."""
    cfg = load_config(config)
    result = validate_aoi(cfg.area_of_interest, cfg.max_area_km2)
    typer.echo(
        json.dumps(
            {
                "label": "OSIT — Open-Source Infrastructure Topology Intelligence",
                "valid": True,
                "aoi_mode": cfg.area_of_interest.mode,
                "area_km2": result.area_km2,
                "notes": result.notes,
            },
            indent=2,
        )
    )


@app.command()
def run(config: Path = typer.Option(Path("config/analysis.yaml"), exists=True)) -> None:
    """Acquire public OSM data, build bounded analytics, and export reproducible artifacts."""
    _configure_logging()
    cfg = load_config(config)
    bundle = collect(cfg)
    output_root = cfg.output_dir
    (output_root / "graphs").mkdir(parents=True, exist_ok=True)
    (output_root / "tables").mkdir(parents=True, exist_ok=True)
    (output_root / "reports").mkdir(parents=True, exist_ok=True)
    (output_root / "provenance").mkdir(parents=True, exist_ok=True)

    prepared = {mode: prepare_graph(graph, mode, cfg.output_crs) for mode, graph in bundle.graphs.items()}
    multimodal = normalized_multimodal_graph(prepared)
    graphml_paths = export_graphml({**prepared, "multimodal": multimodal}, output_root / "graphs")
    gpkg_path = export_geopackage(prepared, output_root / "osit.gpkg")

    metrics: dict[str, dict[str, object]] = {}
    artifacts = [register_artifact(path, "application/graphml+xml") for path in graphml_paths]
    artifacts.append(register_artifact(gpkg_path, "application/geopackage+sqlite3"))
    for mode, graph in prepared.items():
        summary = topology_summary(graph)
        summary["quality"] = graph_quality(graph)
        flags = topology_flags(graph)
        summary["model_identified_articulation_points_count"] = len(flags["model_identified_articulation_points"])
        summary["graph_bridges_count"] = len(flags["graph_bridges"])
        metrics[mode] = summary

        centrality = centrality_table(graph, cfg.max_centrality_nodes)
        centrality_path = export_metric_table(centrality, output_root / "tables" / f"{mode}_node_centrality.parquet")
        artifacts.append(register_artifact(centrality_path, "application/vnd.apache.parquet"))

    summary_payload = {
        "label": "OSIT — Open-Source Infrastructure Topology Intelligence",
        "project_name": cfg.project_name,
        "area_of_interest": str(cfg.area_of_interest.value),
        "area_km2": bundle.area_km2,
        "analysis_date_utc": datetime.now(timezone.utc).isoformat(),
        "network_metrics": metrics,
        "classification_note": "All criticality language is graph-model qualified; no operational targeting claim is made.",
    }
    summary_json = output_root / "tables" / "area_summary.json"
    summary_json.write_text(json.dumps(summary_payload, indent=2, default=str), encoding="utf-8")
    artifacts.append(register_artifact(summary_json, "application/json"))

    brief = write_executive_brief(summary_payload, output_root / "reports" / "executive-brief.md")
    report = write_html_report(summary_payload, output_root / "reports" / "report.html")
    artifacts.extend([register_artifact(brief, "text/markdown"), register_artifact(report, "text/html")])

    manifest = ProvenanceManifest(
        project_name=cfg.project_name,
        sources=list(bundle.sources),
        artifacts=artifacts,
        processing=[
            {"step": "AOI validation", "max_area_km2": cfg.max_area_km2},
            {"step": "OSM acquisition", "cache": str(cfg.cache_dir), "retry_limit": 3},
            {"step": "graph projection", "output_crs": cfg.output_crs},
            {"step": "centrality", "max_exact_nodes": cfg.max_centrality_nodes},
        ],
        limitations=[
            "OpenStreetMap completeness and currency vary.",
            "Estimated speeds/travel times are model assumptions unless a public operational source is supplied.",
            "Topology flags are structural graph metrics, not real-world operational criticality claims.",
        ],
    )
    manifest_path = write_manifest(manifest, output_root / "provenance" / "manifest.json")
    log.info("osit_run_complete", outputs=str(output_root), manifest=str(manifest_path))
    typer.echo(f"OSIT complete: {output_root}")


if __name__ == "__main__":
    app()
