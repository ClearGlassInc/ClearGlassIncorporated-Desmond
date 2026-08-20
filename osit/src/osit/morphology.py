from __future__ import annotations

import math

import networkx as nx


def street_orientation_entropy(graph: nx.MultiDiGraph, bins: int = 36) -> dict[str, float]:
    if bins < 4:
        raise ValueError("at least four orientation bins are required")
    counts = [0] * bins
    observations = 0
    for u, v in graph.edges():
        source = graph.nodes[u]
        target = graph.nodes[v]
        if not all(key in source and key in target for key in ("x", "y")):
            continue
        dx = float(target["x"]) - float(source["x"])
        dy = float(target["y"]) - float(source["y"])
        if dx == 0 and dy == 0:
            continue
        angle = math.degrees(math.atan2(dy, dx)) % 180.0
        index = min(bins - 1, int(angle / 180.0 * bins))
        counts[index] += 1
        observations += 1
    if observations == 0:
        return {"orientation_entropy": 0.0, "orientation_order": 0.0, "observations": 0.0}
    probabilities = [count / observations for count in counts if count]
    entropy = -sum(p * math.log(p) for p in probabilities)
    max_entropy = math.log(bins)
    order = 1.0 - entropy / max_entropy if max_entropy else 0.0
    return {
        "orientation_entropy": entropy,
        "orientation_order": order,
        "observations": float(observations),
    }
