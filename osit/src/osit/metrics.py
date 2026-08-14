from __future__ import annotations

import math
from typing import Any

import networkx as nx
import pandas as pd


def _simple_undirected(graph: nx.MultiDiGraph) -> nx.Graph:
    simple = nx.Graph()
    simple.add_nodes_from(graph.nodes(data=True))
    for u, v, data in graph.edges(data=True):
        length = float(data.get("length", 1.0) or 1.0)
        if length <= 0:
            length = 1.0
        if simple.has_edge(u, v):
            length = min(simple[u][v]["length"], length)
        simple.add_edge(u, v, length=length, strength=1.0 / length)
    return simple


def topology_summary(graph: nx.MultiDiGraph) -> dict[str, Any]:
    simple = _simple_undirected(graph)
    directed_edge_length = sum(
        float(data.get("length", 0.0) or 0.0) for _, _, data in graph.edges(data=True)
    )
    unique_network_length = sum(
        float(data.get("length", 0.0) or 0.0) for _, _, data in simple.edges(data=True)
    )
    degrees = dict(simple.degree())
    intersections = sum(1 for degree in degrees.values() if degree >= 3)
    dead_ends = sum(1 for degree in degrees.values() if degree == 1)
    components = nx.number_connected_components(simple) if simple.number_of_nodes() else 0
    largest = max((len(c) for c in nx.connected_components(simple)), default=0)
    mean_degree = (sum(degrees.values()) / len(degrees)) if degrees else 0.0
    return {
        "node_count": graph.number_of_nodes(),
        "edge_count_directed": graph.number_of_edges(),
        "street_segment_count_undirected": simple.number_of_edges(),
        "total_network_length_m": unique_network_length,
        "directed_edge_length_sum_m": directed_edge_length,
        "intersection_count_degree_ge_3": intersections,
        "dead_end_node_count": dead_ends,
        "connected_components_undirected": components,
        "largest_component_nodes": largest,
        "mean_undirected_degree": mean_degree,
        "average_clustering_undirected": (
            nx.average_clustering(simple) if simple.number_of_nodes() else 0.0
        ),
    }


def centrality_table(graph: nx.MultiDiGraph, max_nodes: int = 7500) -> pd.DataFrame:
    simple = _simple_undirected(graph)
    node_count = simple.number_of_nodes()
    columns = [
        "node",
        "betweenness",
        "closeness",
        "eigenvector",
        "method",
        "eigenvector_weight_basis",
    ]
    if node_count == 0:
        return pd.DataFrame(columns=columns)

    if node_count <= max_nodes:
        betweenness = nx.betweenness_centrality(simple, weight="length", normalized=True)
        closeness = nx.closeness_centrality(simple, distance="length")
        try:
            eigenvector = nx.eigenvector_centrality(
                simple,
                max_iter=1000,
                tol=1e-7,
                weight="strength",
            )
        except nx.PowerIterationFailedConvergence:
            eigenvector = {node: math.nan for node in simple}
        method = "exact-within-configured-bound"
        eigenvector_basis = "inverse-length connection strength"
    else:
        k = min(max(100, int(math.sqrt(node_count) * 10)), max_nodes)
        betweenness = nx.betweenness_centrality(
            simple,
            k=k,
            weight="length",
            normalized=True,
            seed=0,
        )
        closeness = {node: math.nan for node in simple}
        eigenvector = {node: math.nan for node in simple}
        method = f"sampled-betweenness-k={k}; other centralities omitted above bound"
        eigenvector_basis = "omitted above configured node bound"

    rows = [
        {
            "node": node,
            "betweenness": betweenness.get(node, math.nan),
            "closeness": closeness.get(node, math.nan),
            "eigenvector": eigenvector.get(node, math.nan),
            "method": method,
            "eigenvector_weight_basis": eigenvector_basis,
        }
        for node in simple
    ]
    return pd.DataFrame(rows, columns=columns)
