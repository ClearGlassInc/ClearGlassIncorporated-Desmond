from __future__ import annotations

from dataclasses import dataclass

import networkx as nx


@dataclass(frozen=True)
class RemovalScenarioResult:
    removed_edges: int
    baseline_largest_component_fraction: float
    scenario_largest_component_fraction: float
    accessibility_degradation_fraction: float


def topology_flags(graph: nx.MultiDiGraph) -> dict[str, list[object]]:
    simple = nx.Graph(graph)
    articulation = list(nx.articulation_points(simple)) if simple.number_of_nodes() else []
    bridges = [tuple(edge) for edge in nx.bridges(simple)] if simple.number_of_edges() else []
    return {
        "model_identified_articulation_points": articulation,
        "graph_bridges": bridges,
    }


def _largest_component_fraction(graph: nx.Graph) -> float:
    if graph.number_of_nodes() == 0:
        return 0.0
    largest = max((len(c) for c in nx.connected_components(graph)), default=0)
    return largest / graph.number_of_nodes()


def simulate_edge_removal(
    graph: nx.MultiDiGraph,
    edges: list[tuple[object, object]],
) -> RemovalScenarioResult:
    baseline = nx.Graph(graph)
    scenario = baseline.copy()
    removed = 0
    for u, v in edges:
        if scenario.has_edge(u, v):
            scenario.remove_edge(u, v)
            removed += 1
    before = _largest_component_fraction(baseline)
    after = _largest_component_fraction(scenario)
    degradation = max(0.0, before - after)
    return RemovalScenarioResult(removed, before, after, degradation)
