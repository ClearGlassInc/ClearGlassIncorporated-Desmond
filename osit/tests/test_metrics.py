import networkx as nx

from osit.metrics import centrality_table, topology_summary
from osit.resilience import simulate_edge_removal, topology_flags


def line_graph() -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, length=10)
    graph.add_edge(2, 3, length=10)
    return graph


def test_topology_summary() -> None:
    summary = topology_summary(line_graph())
    assert summary["node_count"] == 3
    assert summary["dead_end_node_count"] == 2
    assert summary["connected_components_undirected"] == 1


def test_centrality_table_is_qualified() -> None:
    table = centrality_table(line_graph(), max_nodes=100)
    middle = table.loc[table["node"] == 2].iloc[0]
    assert middle["betweenness"] > 0
    assert middle["method"] == "exact-within-configured-bound"


def test_topology_flags_and_hypothetical_removal() -> None:
    graph = line_graph()
    flags = topology_flags(graph)
    assert 2 in flags["model_identified_articulation_points"]
    result = simulate_edge_removal(graph, [(1, 2)])
    assert result.removed_edges == 1
    assert result.accessibility_degradation_fraction > 0
