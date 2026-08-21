from __future__ import annotations

import re
from collections.abc import Mapping

import networkx as nx
import osmnx as ox
from pyproj import CRS

DEFAULT_KPH = {
    "motorway": 90.0,
    "trunk": 80.0,
    "primary": 60.0,
    "secondary": 50.0,
    "tertiary": 40.0,
    "residential": 30.0,
    "service": 20.0,
    "cycleway": 18.0,
    "footway": 5.0,
    "path": 5.0,
}


def _first(value: object) -> object:
    if isinstance(value, list):
        return value[0] if value else None
    return value


def parse_maxspeed_kph(value: object) -> float | None:
    raw = _first(value)
    if raw is None:
        return None
    text = str(raw).strip().lower()
    match = re.search(r"(\d+(?:\.\d+)?)", text)
    if not match:
        return None
    speed = float(match.group(1))
    if "mph" in text:
        speed *= 1.609344
    return speed if 1 <= speed <= 200 else None


def _default_speed(data: Mapping[str, object], mode: str) -> float:
    if mode == "walk":
        return 5.0
    if mode == "bike":
        return 18.0
    highway = str(_first(data.get("highway")) or "residential")
    return DEFAULT_KPH.get(highway, 30.0)


def add_impedance(graph: nx.MultiDiGraph, mode: str) -> nx.MultiDiGraph:
    for _, _, _, data in graph.edges(keys=True, data=True):
        length_m = float(data.get("length", 0.0) or 0.0)
        tagged_speed = parse_maxspeed_kph(data.get("maxspeed"))
        speed_kph = tagged_speed or _default_speed(data, mode)
        data["speed_kph_est"] = speed_kph
        data["travel_time_s_est"] = (
            length_m / (speed_kph * 1000 / 3600) if speed_kph > 0 else None
        )
        data["travel_time_basis"] = (
            "public maxspeed tag" if tagged_speed else "mode/road-class estimate"
        )
    return graph


def select_metric_crs(graph: nx.MultiDiGraph) -> CRS:
    """Use UTM only for compact single-zone, non-polar graphs; otherwise use local AEQD."""
    nodes, _ = ox.graph_to_gdfs(graph, nodes=True, edges=False)
    if nodes.empty:
        raise ValueError("cannot select metric CRS for an empty graph")
    min_lon, min_lat, max_lon, max_lat = nodes.total_bounds
    centroid = nodes.geometry.unary_union.centroid
    lon, lat = float(centroid.x), float(centroid.y)
    width = max_lon - min_lon
    zone_min = int((min_lon + 180) // 6) + 1
    zone_max = int((max_lon + 180) // 6) + 1
    if -80 <= lat <= 84 and zone_min == zone_max and width <= 6.0:
        epsg = (32600 if lat >= 0 else 32700) + zone_min
        return CRS.from_epsg(epsg)
    return CRS.from_proj4(
        f"+proj=aeqd +lat_0={lat:.8f} +lon_0={lon:.8f} +datum=WGS84 +units=m +no_defs"
    )


def prepare_graph(
    graph: nx.MultiDiGraph,
    mode: str,
    output_crs: str = "auto_local_metric",
) -> nx.MultiDiGraph:
    prepared = graph.copy()
    add_impedance(prepared, mode)
    if output_crs in {"auto_utm", "auto_local_metric"}:
        target_crs = select_metric_crs(prepared)
        prepared = ox.project_graph(prepared, to_crs=target_crs)
        prepared.graph["osit_metric_crs_selection"] = target_crs.to_string()
    else:
        prepared = ox.project_graph(prepared, to_crs=output_crs)
        prepared.graph["osit_metric_crs_selection"] = str(output_crs)
    prepared.graph["osit_mode"] = mode
    return prepared


def component_metrics(graph: nx.MultiDiGraph) -> tuple[int, int]:
    if graph.number_of_nodes() == 0:
        return 0, 0
    components = list(nx.weakly_connected_components(graph))
    largest = max((len(component) for component in components), default=0)
    return len(components), largest


def largest_component_for_analysis(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """Explicitly select the largest component without mutating the preserved source graph."""
    if graph.number_of_nodes() == 0:
        return graph.copy()
    component = max(nx.weakly_connected_components(graph), key=len)
    return graph.subgraph(component).copy()


def graph_quality(graph: nx.MultiDiGraph) -> dict[str, int]:
    isolated = sum(1 for node in graph if graph.degree(node) == 0)
    undirected = nx.Graph(graph)
    duplicate_pairs = graph.number_of_edges() - undirected.number_of_edges()
    components, largest = component_metrics(graph)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "isolated_nodes": isolated,
        "components": components,
        "largest_component_nodes": largest,
        "parallel_or_directional_edge_excess": max(0, duplicate_pairs),
    }
