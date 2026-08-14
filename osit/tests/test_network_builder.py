import networkx as nx

from osit.network_builder import add_impedance, graph_quality, parse_maxspeed_kph


def test_parse_maxspeed() -> None:
    assert parse_maxspeed_kph("50") == 50.0
    assert round(parse_maxspeed_kph("30 mph") or 0, 3) == 48.280
    assert parse_maxspeed_kph(None) is None


def test_add_impedance_discloses_estimate() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, length=1000.0, highway="residential")
    add_impedance(graph, "drive")
    data = graph[1][2][0]
    assert data["speed_kph_est"] == 30.0
    assert round(data["travel_time_s_est"], 2) == 120.0
    assert data["travel_time_basis"] == "mode/road-class estimate"


def test_graph_quality_counts_components() -> None:
    graph = nx.MultiDiGraph()
    graph.add_edge(1, 2, length=10)
    graph.add_node(3)
    result = graph_quality(graph)
    assert result["nodes"] == 3
    assert result["isolated_nodes"] == 1
    assert result["components"] == 2
