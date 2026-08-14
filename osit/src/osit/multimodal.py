from __future__ import annotations

import networkx as nx


def normalized_multimodal_graph(graphs: dict[str, nx.MultiDiGraph]) -> nx.MultiDiGraph:
    """Compose mode graphs without inventing physical transfer links.

    Nodes are namespaced by mode. Transfer edges require authoritative stop/entrance linkage or an
    explicitly documented proximity model and are therefore not fabricated by this core routine.
    """
    combined = nx.MultiDiGraph()
    combined.graph["label"] = "OSIT — Open-Source Infrastructure Topology Intelligence"
    combined.graph["transfer_policy"] = "no inferred transfer links in core MVP"
    for mode, graph in graphs.items():
        mapping = {node: f"{mode}:{node}" for node in graph.nodes}
        relabeled = nx.relabel_nodes(graph, mapping, copy=True)
        for _, attrs in relabeled.nodes(data=True):
            attrs["mode"] = mode
        for _, _, _, attrs in relabeled.edges(keys=True, data=True):
            attrs["mode"] = mode
        combined = nx.compose(combined, relabeled)
    return combined
