from __future__ import annotations

import re
from collections.abc import Mapping

import networkx as nx
import osmnx as ox

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
    if mode == "transit_rail":
        return 35.0
    highway = str(_first(data.get("highway")) or "residential")
    return DEFAULT_KPH.get(highway, 30.0)


def add_impedance(graph: nx.MultiDiGraph, mode: str) -> nx.MultiDiGraph:
    for _, _, _, data in graph.edges(keys=True, data=True):
        length_m = float(data.get("length", 0.0) or 0.0)
        speed_kph = parse_maxspeed_kph(data.get("maxspeed")) or _default_speed(data, mode)
        data["speed_kph_est"] = speed_kph
        data["travel_time_s_est"] = (length_m / (speed_kph * 1000 / 3600)) if speed_kph > 0 else None
        data["travel_time_basis"] = (
            "public maxspeed tag" if parse_maxspeed_kph(data.get("maxspeed")) else "mode/road-class estimate"
        )
    return graph


def prepare_graph(graph: nx.MultiDiGraph, mode: str, output_crs: str = "auto_utm") -> nx.MultiDiGraph:
    prepared = graph.copy()
    add_impedance(prepared, mode)
    if output_crs == "auto_utm":
        prepared = ox.project_graph(prepared)
    else:
        prepared = ox.project_graph(prepared, to_crs=output_crs)
    prepared.graph["osit_mode"] = mode
    return prepared


def graph_quality(graph: nx.MultiDiGraph) -> dict[str, int]:
    isolated = sum(1 for node in graph if graph.degree(node) == 0)
    undirected = nx.Graph(graph)
    duplicate_pairs = graph.number_of_edges() - undirected.number_of_edges()
    if graph.is_directed():
        components = nx.number_weakly_connected_components(graph)
    else:
        components = nx.number_connected_components(graph)
    return {
        "nodes": graph.number_of_nodes(),
        "edges": graph.number_of_edges(),
        "isolated_nodes": isolated,
        "components": components,
        "parallel_or_directional_edge_excess": max(0, duplicate_pairs),
    }
