from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated

import structlog
import typer

from .acquisition import collect, effective_osmnx_settings
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
    write_geojson,
    write_html_report,
)

app = typer.Typer(help="OSIT — Open-Source Infrastructure Topology Intelligence")
log = structlog.get_logger("osit")
ConfigPath = Annotated[Path, typer.Option(exists=True, dir_okay=False, readable=True)]


def _configure_logging() -> None:
    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ]
    )


@app.command()
def validate(config: ConfigPath = Path("config/analysis.yaml")) -> None:
    """Validate configuration and non-place AOI geometry without acquiring networks."""
    cfg = load_config(config)
    result = validate_aoi(cfg.area_of_interest, cfg.max_area_km2, cfg.repair_invalid_aoi)
    typer.echo(
        json.dumps(
            {
                "label": "OSIT — Open-Source Infrastructure Topology Intelligence",
                "valid": True,
                "aoi_mode": cfg.area_of_interest.mode,
                "area_km2": result.area_km2,
                "repair_invalid_aoi": cfg.repair_invalid_aoi,
                "notes": result.notes,
            },
            indent=2,
        )
    )


@app.command()
def run(config: ConfigPath = Path("config/analysis.yaml")) -> None:
    """Acquire public OSM data, build bounded analytics, and export reproducible artifacts."""
    _configure_logging()
    cfg = load_config(config)
    bundle = collect(cfg)
    output_root = cfg.output_dir
    for directory in ("graphs", "tables", "reports", "provenance"):
        (output_root / directory).mkdir(parents=True, exist_ok=True)

    prepared = {
        mode: prepare_graph(graph, mode, cfg.output_crs)
        for mode, graph in bundle.graphs.items()
    }
    multimodal = normalized_multimodal_graph(prepared)
    graphml_paths = export_graphml(
        {**prepared, "multimodal": multimodal},
        output_root / "graphs",
    )
    gpkg_path = export_geopackage(prepared, output_root / "osit.gpkg")

    artifacts = [register_artifact(path, "application/graphml+xml") for path in graphml_paths]
    artifacts.append(register_artifact(gpkg_path, "application/geopackage+sqlite3"))

    if bundle.rail_features is not None:
        rail_geojson = write_geojson(
            bundle.rail_features,
            output_root / "tables" / "transit_rail_features.geojson",
        )
        rail_parquet = output_root / "tables" / "transit_rail_features.parquet"
        bundle.rail_features.to_parquet(rail_parquet, index=False)
        artifacts.extend(
            [
                register_artifact(rail_geojson, "application/geo+json"),
                register_artifact(rail_parquet, "application/vnd.apache.parquet"),
            ]
        )

    metrics: dict[str, dict[str, object]] = {}
    for mode, graph in prepared.items():
        summary = topology_summary(graph)
        summary["quality"] = graph_quality(graph)
        flags = topology_flags(graph)
        summary["model_identified_articulation_points_count"] = len(
            flags["model_identified_articulation_points"]
        )
        summary["graph_bridges_count"] = len(flags["graph_bridges"])
        metrics[mode] = summary

        centrality = centrality_table(graph, cfg.max_centrality_nodes)
        centrality_path = export_metric_table(
            centrality,
            output_root / "tables" / f"{mode}_node_centrality.parquet",
        )
        artifacts.append(register_artifact(centrality_path, "application/vnd.apache.parquet"))

    summary_payload = {
        "label": "OSIT — Open-Source Infrastructure Topology Intelligence",
        "project_name": cfg.project_name,
        "area_of_interest": str(cfg.area_of_interest.value),
        "area_km2": bundle.area_km2,
        "analysis_date_utc": datetime.now(UTC).isoformat(),
        "network_modes_requested": cfg.network_modes,
        "network_modes_routable": list(prepared),
        "transit_rail": (
            {
                "feature_count": len(bundle.rail_features),
                "routability": "non_routable_feature_layer",
            }
            if bundle.rail_features is not None
            else None
        ),
        "network_metrics": metrics,
        "osmnx": effective_osmnx_settings(),
        "classification_note": (
            "All criticality language is graph-model qualified; no operational targeting claim is made."
        ),
    }
    summary_json = output_root / "tables" / "area_summary.json"
    summary_json.write_text(
        json.dumps(summary_payload, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8",
    )
    artifacts.append(register_artifact(summary_json, "application/json"))

    brief = write_executive_brief(summary_payload, output_root / "reports" / "executive-brief.md")
    report = write_html_report(summary_payload, output_root / "reports" / "report.html")
    artifacts.extend(
        [
            register_artifact(brief, "text/markdown"),
            register_artifact(report, "text/html"),
        ]
    )

    sources = [*bundle.sources]
    if bundle.rail_source is not None:
        sources.append(bundle.rail_source)

    manifest = ProvenanceManifest(
        project_name=cfg.project_name,
        sources=sources,
        artifacts=artifacts,
        processing=[
            {
                "step": "AOI validation",
                "repair_invalid_aoi": cfg.repair_invalid_aoi,
                "max_area_km2": cfg.max_area_km2,
            },
            {
                "step": "OSM acquisition",
                "cache": str(cfg.cache_dir),
                "retry_limit": cfg.overpass_max_retries,
                "effective_settings": effective_osmnx_settings(),
                "network_mode_policy": "one acquisition per requested mode",
                "transit_rail_policy": "separate feature-layer acquisition; not a routable street graph",
            },
            {
                "step": "graph projection",
                "output_crs": cfg.output_crs,
                "metric_crs_policy": "single-zone UTM when suitable, otherwise local AEQD",
            },
            {
                "step": "component preservation",
                "retain_all_components": cfg.retain_all_components,
                "largest_component_selection": "explicit analysis operation only",
            },
            {"step": "centrality", "max_exact_nodes": cfg.max_centrality_nodes},
        ],
        limitations=[
            "OpenStreetMap completeness and currency vary.",
            "Place-name geocoding can resolve to a broad administrative boundary; review the resolved AOI before consequential use.",
            "Estimated travel times are model assumptions unless authoritative operational speed/schedule data are supplied.",
            "Rail is a feature layer only until GTFS/service data and station-link validation pass.",
            "OSM tags do not establish legal access, safety, accessibility, or operational status unless corroborated by authoritative sources.",
        ],
    )
    manifest_path = write_manifest(manifest, output_root / "provenance" / "manifest.json")
    log.info("osit_run_complete", outputs=str(output_root), manifest=str(manifest_path))
    typer.echo(f"OSIT complete: {output_root}")


if __name__ == "__main__":
    app()
