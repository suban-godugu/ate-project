"""Similarity analysis between failure signatures."""

from __future__ import annotations

from typing import Any


def analyze_similarity(
    failure_rows: list[dict[str, Any]],
    *,
    threshold: float = 0.75,
) -> dict[str, Any]:
    """Detect similar failure signatures using Jaccard overlap on attribute sets."""
    signatures = [_signature_set(row) for row in failure_rows]
    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    for i in range(len(failure_rows)):
        for j in range(i + 1, len(failure_rows)):
            a = failure_rows[i]
            b = failure_rows[j]
            key_a = _row_key(a)
            key_b = _row_key(b)
            pair_key = tuple(sorted((key_a, key_b)))
            if pair_key in seen:
                continue
            seen.add(pair_key)

            score = _jaccard(signatures[i], signatures[j])
            if score < threshold:
                continue
            pairs.append(
                {
                    "left": key_a,
                    "right": key_b,
                    "similarity_score": round(score, 4),
                    "shared_attributes": sorted(signatures[i] & signatures[j]),
                    "pattern_match": a.get("pattern_id") == b.get("pattern_id"),
                    "lot_match": a.get("lot_id") == b.get("lot_id"),
                }
            )

    pairs.sort(key=lambda p: p["similarity_score"], reverse=True)
    groups = _group_similar(pairs, threshold)
    return {
        "similarity_threshold": threshold,
        "pair_count": len(pairs),
        "similar_pairs": pairs[:100],
        "similarity_groups": groups[:25],
    }


def merge_similar_events(
    events: list[dict[str, Any]],
    similarity_report: dict[str, Any],
) -> list[dict[str, Any]]:
    """Deduplicate recurrence events that represent the same underlying signature."""
    if not events:
        return []

    entity_index: dict[str, dict[str, Any]] = {}
    for event in events:
        dedupe_key = f"{event.get('signature_type')}::{event.get('entity_key')}"
        if dedupe_key in entity_index:
            existing = entity_index[dedupe_key]
            existing["failure_count"] = int(existing.get("failure_count", 0)) + int(
                event.get("failure_count", 0)
            )
            existing["entity_count"] = max(
                int(existing.get("entity_count", 0)), int(event.get("entity_count", 0))
            )
            for field in ("lot_keys", "wafer_keys", "die_keys"):
                merged = set(existing.get(field, [])) | set(event.get(field, []))
                existing[field] = sorted(merged)
            existing["confidence"] = max(
                float(existing.get("confidence", 0)), float(event.get("confidence", 0))
            )
        else:
            entity_index[dedupe_key] = dict(event)

    return sorted(
        entity_index.values(),
        key=lambda e: (e.get("confidence", 0), e.get("failure_count", 0)),
        reverse=True,
    )


def _signature_set(row: dict[str, Any]) -> set[str]:
    parts = {
        f"pattern:{row.get('pattern_id', '')}",
        f"lot:{row.get('lot_id', '')}",
        f"wafer:{row.get('wafer_id', '')}",
        f"die:{row.get('die_id', '')}",
        f"device:{row.get('device_id', '')}",
        f"product:{row.get('product_id', '')}",
        f"tester:{row.get('tester_id', '')}",
        f"bin:{row.get('hard_bin', '')}",
        f"time:{row.get('time_window', '')}",
    }
    return {p for p in parts if not p.endswith(":")}


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union = a | b
    if not union:
        return 0.0
    return len(a & b) / len(union)


def _row_key(row: dict[str, Any]) -> str:
    return (
        f"{row.get('lot_id')}|{row.get('wafer_id')}|{row.get('die_id')}|"
        f"{row.get('pattern_id')}"
    )


def _group_similar(
    pairs: list[dict[str, Any]],
    threshold: float,
) -> list[dict[str, Any]]:
    parent: dict[str, str] = {}

    def find(node: str) -> str:
        parent.setdefault(node, node)
        if parent[node] != node:
            parent[node] = find(parent[node])
        return parent[node]

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[rb] = ra

    for pair in pairs:
        if pair["similarity_score"] >= threshold:
            union(pair["left"], pair["right"])

    groups: dict[str, list[str]] = {}
    for node in parent:
        root = find(node)
        groups.setdefault(root, []).append(node)

    return [
        {"group_id": root, "members": sorted(members), "size": len(members)}
        for root, members in groups.items()
        if len(members) > 1
    ]
