from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import geopandas as gpd
import networkx as nx
import osmnx as ox
from shapely.geometry.base import BaseGeometry
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import AreaOfInterest, NetworkMode, OSITConfig
from .provenance import SourceRecord, canonical_sha256
from .validation import AOIValidationResult, validate_aoi, validate_resolved_geometry


class AcquisitionError(RuntimeError):
    """Raised when a public-source acquisition cannot be completed safely."""


@dataclass(frozen=True)
class AcquisitionBundle:
    geometry: BaseGeometry
    area_km2: float
    graphs: dict[str, nx.MultiDiGraph]
    sources: tuple[SourceRecord, ...]
    rail_features: gpd.GeoDataFrame | None = None
    rail_source: SourceRecord | None = None


def configure_osmnx(config: OSITConfig) -> None:
    cache_dir = Path(config.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(cache_dir)
    ox.settings.log_console = False
    ox.settings.requests_timeout = config.request_timeout_seconds
    if config.overpass_url:
        ox.settings.overpass_url = config.overpass_url


def effective_osmnx_settings() -> dict[str, Any]:
    return {
        "osmnx_version": ox.__version__,
        "overpass_url": str(getattr(ox.settings, "overpass_url", "")),
        "requests_timeout": getattr(ox.settings, "requests_timeout", None),
        "use_cache": getattr(ox.settings, "use_cache", None),
        "cache_folder": str(getattr(ox.settings, "cache_folder", "")),
    }


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def _resolve_place(place: str) -> BaseGeometry:
    result = ox.geocode_to_gdf(place)
    if result.empty:
        raise AcquisitionError(f"place could not be resolved: {place}")
    geometry = result.geometry.iloc[0]
    if geometry.geom_type not in {"Polygon", "MultiPolygon"}:
        raise AcquisitionError("resolved place has no polygonal boundary")
    return geometry


def resolve_geometry(config: OSITConfig) -> tuple[BaseGeometry, float, tuple[str, ...]]:
    result: AOIValidationResult = validate_aoi(
        config.area_of_interest,
        config.max_area_km2,
        config.repair_invalid_aoi,
    )
    if result.geometry is not None and result.area_km2 is not None:
        return result.geometry, result.area_km2, result.notes

    geometry = _resolve_place(str(config.area_of_interest.value))
    area_km2 = validate_resolved_geometry(geometry, config.max_area_km2)
    return geometry, area_km2, (
        "place_name resolved through OSMnx geocoding; resolved boundary validated before acquisition",
    )


def _network_kwargs(mode: NetworkMode, config: OSITConfig) -> dict[str, Any]:
    if mode == "transit_rail":
        raise ValueError("transit_rail is a separate feature layer, not an OSMnx street-network mode")
    return {
        "network_type": mode,
        "retain_all": config.retain_all_components,
        "simplify": config.simplify_network,
        "truncate_by_edge": True,
    }


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def fetch_network(geometry: BaseGeometry, mode: NetworkMode, config: OSITConfig) -> nx.MultiDiGraph:
    graph = ox.graph_from_polygon(geometry, **_network_kwargs(mode, config))
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise AcquisitionError(f"OSM returned an empty {mode} graph")
    graph.graph.update(
        {
            "osit_mode": mode,
            "osit_source": "OpenStreetMap / Overpass",
            "osit_retain_all_components": config.retain_all_components,
        }
    )
    return graph


RAIL_TAGS = {
    "railway": ["rail", "light_rail", "subway", "tram", "station", "halt"],
    "public_transport": ["station", "stop_position", "platform"],
}


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(5),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    reraise=True,
)
def fetch_public_rail_features(geometry: BaseGeometry) -> gpd.GeoDataFrame:
    rail = ox.features_from_polygon(geometry, tags=RAIL_TAGS)
    if rail.empty:
        return rail
    rail = rail.reset_index()
    rail = rail[rail.geometry.notna()].copy()
    rail = rail.set_crs("EPSG:4326", allow_override=True)
    rail["osit_mode"] = "transit_rail"
    rail["osit_routability"] = "non_routable_feature_layer"
    return rail


def collect(config: OSITConfig) -> AcquisitionBundle:
    configure_osmnx(config)
    geometry, area_km2, aoi_notes = resolve_geometry(config)
    graphs: dict[str, nx.MultiDiGraph] = {}
    sources: list[SourceRecord] = []
    rail_features: gpd.GeoDataFrame | None = None
    rail_source: SourceRecord | None = None

    for mode in config.network_modes:
        if mode == "transit_rail":
            rail_features = fetch_public_rail_features(geometry)
            rail_source = SourceRecord(
                source_name="OpenStreetMap / transit_rail feature layer",
                source_url="https://www.openstreetmap.org/",
                license="ODbL 1.0",
                query_parameters={
                    "network_mode": "transit_rail",
                    "feature_tags": RAIL_TAGS,
                    "aoi_mode": config.area_of_interest.mode,
                    "effective_osmnx_settings": effective_osmnx_settings(),
                },
                geographic_coverage=str(config.area_of_interest.value),
                coordinate_reference_system=str(rail_features.crs or "EPSG:4326"),
                data_quality_notes=(
                    "Rail is retained as a distinct non-routable feature layer. Routing remains unavailable "
                    "without validated station/entrance linkage, service data, and transfer rules."
                ),
                dataset_sha256=canonical_sha256(rail_features),
                feature_count=len(rail_features),
                notes=list(aoi_notes),
            )
            continue

        graph = fetch_network(geometry, mode, config)
        graphs[mode] = graph
        _, edges = ox.graph_to_gdfs(graph, nodes=False, edges=True)
        sources.append(
            SourceRecord(
                source_name=f"OpenStreetMap / {mode}",
                source_url="https://www.openstreetmap.org/",
                license="ODbL 1.0",
                query_parameters={
                    "network_mode": mode,
                    "aoi_mode": config.area_of_interest.mode,
                    "retain_all_components": config.retain_all_components,
                    "simplify_network": config.simplify_network,
                    "effective_osmnx_settings": effective_osmnx_settings(),
                },
                geographic_coverage=str(config.area_of_interest.value),
                coordinate_reference_system=str(graph.graph.get("crs", "EPSG:4326")),
                data_quality_notes=(
                    "OpenStreetMap is community-maintained. Component preservation prevents silently "
                    "discarding disconnected infrastructure; completeness and currency are not guaranteed."
                ),
                dataset_sha256=canonical_sha256(edges),
                node_count=graph.number_of_nodes(),
                edge_count=graph.number_of_edges(),
                notes=list(aoi_notes),
            )
        )

    return AcquisitionBundle(
        geometry=geometry,
        area_km2=area_km2,
        graphs=graphs,
        sources=tuple(sources),
        rail_features=rail_features,
        rail_source=rail_source,
    )
