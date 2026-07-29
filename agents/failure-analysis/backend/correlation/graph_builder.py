"""NetworkX relationship graph builder for failure correlations."""

from __future__ import annotations

from typing import Any

try:
    import networkx as nx

    NETWORKX_AVAILABLE = True
except ImportError:  # pragma: no cover
    NETWORKX_AVAILABLE = False
    nx = None  # type: ignore


def build_relationship_graph(
    *,
    correlation_matrix: dict[str, Any],
    association_rules: list[dict[str, Any]],
    pattern_relationships: list[dict[str, Any]],
    dimension_correlations: dict[str, Any],
    threshold: float = 0.35,
) -> dict[str, Any]:
    """Build failure dependency graph from correlation outputs."""
    if not NETWORKX_AVAILABLE:
        return _fallback_graph(
            correlation_matrix, association_rules, pattern_relationships, dimension_correlations
        )

    graph = nx.Graph()

    for dim, info in dimension_correlations.items():
        graph.add_node(
            dim,
            node_type="dimension",
            correlation_score=info.get("correlation_score", 0.0),
        )
        graph.add_node("failure", node_type="outcome")
        graph.add_edge(
            dim,
            "failure",
            weight=info.get("correlation_score", 0.0),
            method=info.get("method", "chi_square"),
        )

    for pair in correlation_matrix.get("significant_pairs", []):
        left, right = pair["left"], pair["right"]
        graph.add_node(left, node_type="numeric")
        graph.add_node(right, node_type="numeric")
        graph.add_edge(
            left,
            right,
            weight=abs(pair["correlation_score"]),
            method=pair["method"],
        )

    for rule in association_rules[:25]:
        ant = rule["antecedent"]
        con = rule["consequent"]
        graph.add_node(ant, node_type="category")
        graph.add_node(con, node_type="category")
        graph.add_edge(
            ant,
            con,
            weight=rule["confidence"],
            method="association_rule",
            support=rule["support"],
            lift=rule["lift"],
        )

    for rel in pattern_relationships[:25]:
        pid = rel.get("pattern_id", "UNKNOWN")
        graph.add_node(pid, node_type="pattern", correlation_score=rel.get("correlation_score"))
        for dim in ("tester", "lot", "product"):
            dim_key = rel.get(f"top_{dim}")
            if dim_key:
                node = f"{dim}={dim_key}"
                graph.add_node(node, node_type="category")
                graph.add_edge(
                    pid,
                    node,
                    weight=rel.get("correlation_score", 0.0),
                    method="pattern_correlation",
                )

    nodes = [
        {
            "id": node,
            "node_type": data.get("node_type", "unknown"),
            "correlation_score": data.get("correlation_score"),
        }
        for node, data in graph.nodes(data=True)
    ]
    edges = [
        {
            "source": u,
            "target": v,
            "weight": round(float(data.get("weight", 0.0)), 4),
            "method": data.get("method", ""),
        }
        for u, v, data in graph.edges(data=True)
        if float(data.get("weight", 0.0)) >= threshold
    ]

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "density": round(nx.density(graph), 4) if graph.number_of_nodes() > 1 else 0.0,
        "layout": _spring_layout(graph) if graph.number_of_nodes() else {},
    }


def _spring_layout(graph: Any) -> dict[str, dict[str, float]]:
    if graph.number_of_nodes() == 0:
        return {}
    pos = nx.spring_layout(graph, seed=42)
    return {
        node: {"x": round(float(coords[0]), 4), "y": round(float(coords[1]), 4)}
        for node, coords in pos.items()
    }


def _fallback_graph(
    correlation_matrix: dict[str, Any],
    association_rules: list[dict[str, Any]],
    pattern_relationships: list[dict[str, Any]],
    dimension_correlations: dict[str, Any],
) -> dict[str, Any]:
    nodes = [{"id": dim, "node_type": "dimension"} for dim in dimension_correlations]
    edges = [
        {
            "source": dim,
            "target": "failure",
            "weight": info.get("correlation_score", 0.0),
            "method": info.get("method", ""),
        }
        for dim, info in dimension_correlations.items()
    ]
    for rule in association_rules[:25]:
        edges.append(
            {
                "source": rule["antecedent"],
                "target": rule["consequent"],
                "weight": rule["confidence"],
                "method": "association_rule",
            }
        )
    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "nodes": nodes,
        "edges": edges,
        "density": 0.0,
        "layout": {},
        "method": "fallback",
    }
