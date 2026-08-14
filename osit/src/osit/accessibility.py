from __future__ import annotations

import networkx as nx


def reachable_nodes(
    graph: nx.MultiDiGraph,
    origin: object,
    threshold_minutes: int,
    weight: str = "travel_time_s_est",
) -> set[object]:
    if origin not in graph:
        raise KeyError(f"origin node not present in graph: {origin}")
    cutoff = threshold_minutes * 60
    distances = nx.single_source_dijkstra_path_length(graph, origin, cutoff=cutoff, weight=weight)
    return set(distances)


def isochrone_subgraph(
    graph: nx.MultiDiGraph,
    origin: object,
    threshold_minutes: int,
    weight: str = "travel_time_s_est",
) -> nx.MultiDiGraph:
    nodes = reachable_nodes(graph, origin, threshold_minutes, weight)
    result = graph.subgraph(nodes).copy()
    result.graph["osit_model"] = "network-constrained isochrone"
    result.graph["threshold_minutes"] = threshold_minutes
    result.graph["weight"] = weight
    return result


def nearest_service_distance(
    graph: nx.MultiDiGraph,
    origin: object,
    destination_nodes: set[object],
    weight: str = "travel_time_s_est",
) -> tuple[object | None, float | None]:
    if origin not in graph:
        raise KeyError(f"origin node not present in graph: {origin}")
    if not destination_nodes:
        return None, None
    lengths = nx.single_source_dijkstra_path_length(graph, origin, weight=weight)
    candidates = [(node, lengths[node]) for node in destination_nodes if node in lengths]
    return min(candidates, key=lambda item: item[1]) if candidates else (None, None)
