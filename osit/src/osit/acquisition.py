from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import networkx as nx
import osmnx as ox
from shapely.geometry.base import BaseGeometry
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .config import NetworkMode, OSITConfig
from .provenance import SourceRecord
from .validation import validate_aoi, validate_resolved_geometry


class AcquisitionError(RuntimeError):
    """Raised when a public-source acquisition cannot be completed safely."""


@dataclass(frozen=True)
class AcquisitionBundle:
    geometry: BaseGeometry
    area_km2: float
    graphs: dict[str, nx.MultiDiGraph]
    sources: tuple[SourceRecord, ...]


def configure_osmnx(cache_dir: str | Path) -> None:
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(Path(cache_dir))
    ox.settings.log_console = False
    ox.settings.requests_timeout = 60


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
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


def resolve_geometry(config: OSITConfig) -> tuple[BaseGeometry, float]:
    initial = validate_aoi(config.area_of_interest, config.max_area_km2)
    if initial.geometry is not None and initial.area_km2 is not None:
        return initial.geometry, initial.area_km2
    geometry = _resolve_place(str(config.area_of_interest.value))
    area_km2 = validate_resolved_geometry(geometry, config.max_area_km2)
    return geometry, area_km2


def _network_kwargs(mode: NetworkMode) -> dict[str, Any]:
    if mode == "transit_rail":
        return {
            "network_type": "all",
            "custom_filter": '["railway"~"rail|tram|subway|light_rail"]',
            "retain_all": True,
            "simplify": True,
        }
    return {"network_type": mode, "retain_all": True, "simplify": True}


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=20),
    reraise=True,
)
def fetch_network(geometry: BaseGeometry, mode: NetworkMode) -> nx.MultiDiGraph:
    graph = ox.graph_from_polygon(geometry, **_network_kwargs(mode))
    if graph.number_of_nodes() == 0 or graph.number_of_edges() == 0:
        raise AcquisitionError(f"OSM returned an empty {mode} graph")
    graph.graph["osit_mode"] = mode
    graph.graph["osit_source"] = "OpenStreetMap"
    return graph


def collect(config: OSITConfig) -> AcquisitionBundle:
    configure_osmnx(config.cache_dir)
    geometry, area_km2 = resolve_geometry(config)
    graphs: dict[str, nx.MultiDiGraph] = {}
    sources: list[SourceRecord] = []
    for mode in config.network_modes:
        graph = fetch_network(geometry, mode)
        graphs[mode] = graph
        sources.append(
            SourceRecord(
                source_name=f"OpenStreetMap/{mode}",
                source_url="https://www.openstreetmap.org/",
                license="ODbL 1.0",
                query_parameters={"network_mode": mode, "aoi_mode": config.area_of_interest.mode},
                geographic_coverage=str(config.area_of_interest.value),
                coordinate_reference_system=str(graph.graph.get("crs", "EPSG:4326")),
                data_quality_notes=(
                    "Public volunteered geographic information. Tag completeness, topology, and currency vary; "
                    "map completeness does not establish real-world completeness."
                ),
            )
        )
    return AcquisitionBundle(geometry, area_km2, graphs, tuple(sources))
