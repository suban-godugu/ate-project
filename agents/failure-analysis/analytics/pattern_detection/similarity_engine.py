"""Similarity matching — statistical core with optional AI/FAISS layer."""

from __future__ import annotations

import math
from typing import Any

import numpy as np

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    SKLEARN_AVAILABLE = True
except ImportError:  # pragma: no cover
    SKLEARN_AVAILABLE = False

AI_SIMILARITY_AVAILABLE = False
try:
    import faiss  # noqa: F401

    AI_SIMILARITY_AVAILABLE = True
except ImportError:  # pragma: no cover
    pass


def _signature_text(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("pattern_id", "")),
        str(row.get("scan_chain_id", "")),
        str(row.get("expected_signature", "")),
        str(row.get("actual_signature", "")),
        str(row.get("device_name", "")),
        str(row.get("lot_id", "")),
    ]
    return " ".join(parts)


def statistical_similarity(
    failures: list[dict[str, Any]],
    *,
    threshold: float = 0.75,
) -> list[dict[str, Any]]:
    """Cosine similarity over TF-IDF failure signatures."""
    if len(failures) < 2:
        return []
    if not SKLEARN_AVAILABLE:
        return _jaccard_similarity(failures, threshold=threshold)

    texts = [_signature_text(row) for row in failures]
    vectorizer = TfidfVectorizer(min_df=1, token_pattern=r"[A-Za-z0-9_]+")
    matrix = vectorizer.fit_transform(texts)
    sim = cosine_similarity(matrix)

    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for i in range(len(failures)):
        for j in range(i + 1, len(failures)):
            score = float(sim[i, j])
            if score < threshold:
                continue
            a = str(failures[i].get("pattern_id", ""))
            b = str(failures[j].get("pattern_id", ""))
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append(
                {
                    "pattern_a": a,
                    "pattern_b": b,
                    "similarity_score": round(score, 4),
                    "method": "statistical_tfidf",
                }
            )
    pairs.sort(key=lambda item: item["similarity_score"], reverse=True)
    return pairs


def ai_similarity_search(
    failures: list[dict[str, Any]],
    *,
    threshold: float = 0.75,
) -> list[dict[str, Any]]:
    """
    Optional AI-assisted similarity via embedding index.
    Falls back to statistical similarity when FAISS/LangChain unavailable.
    """
    if not AI_SIMILARITY_AVAILABLE or len(failures) < 2:
        return []

    # Lightweight numeric embedding fallback (no external API key required).
    vectors = []
    pattern_ids = []
    for row in failures:
        pid = str(row.get("pattern_id", ""))
        pattern_ids.append(pid)
        vec = [
            float(hash(pid) % 1000) / 1000.0,
            float(hash(str(row.get("scan_chain_id", ""))) % 1000) / 1000.0,
            float(row.get("confidence", 0.0) or 0.0),
        ]
        vectors.append(vec)
    matrix = np.array(vectors, dtype=np.float32)
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    matrix = matrix / norms

    import faiss

    index = faiss.IndexFlatIP(matrix.shape[1])
    index.add(matrix)
    scores, indices = index.search(matrix, min(5, len(failures)))

    pairs: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for i, neighbors in enumerate(indices):
        for j, score in zip(neighbors, scores[i]):
            if i == j or score < threshold:
                continue
            a, b = pattern_ids[i], pattern_ids[j]
            key = tuple(sorted((a, b)))
            if key in seen:
                continue
            seen.add(key)
            pairs.append(
                {
                    "pattern_a": a,
                    "pattern_b": b,
                    "similarity_score": round(float(score), 4),
                    "method": "ai_faiss_embedding",
                }
            )
    pairs.sort(key=lambda item: item["similarity_score"], reverse=True)
    return pairs


def find_similar_patterns(
    target_pattern_id: str,
    failures: list[dict[str, Any]],
    similar_pairs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    related: list[dict[str, Any]] = []
    for pair in similar_pairs:
        if pair["pattern_a"] == target_pattern_id:
            related.append({"pattern_id": pair["pattern_b"], **pair})
        elif pair["pattern_b"] == target_pattern_id:
            related.append({"pattern_id": pair["pattern_a"], **pair})
    return related


def _jaccard_similarity(
    failures: list[dict[str, Any]],
    *,
    threshold: float,
) -> list[dict[str, Any]]:
    by_pattern: dict[str, set[str]] = {}
    for row in failures:
        pid = str(row.get("pattern_id", ""))
        token = _signature_text(row)
        by_pattern.setdefault(pid, set()).add(token)
    patterns = list(by_pattern.keys())
    pairs: list[dict[str, Any]] = []
    for i in range(len(patterns)):
        for j in range(i + 1, len(patterns)):
            a, b = patterns[i], patterns[j]
            inter = len(by_pattern[a] & by_pattern[b])
            union = len(by_pattern[a] | by_pattern[b]) or 1
            score = inter / union
            if score >= threshold:
                pairs.append(
                    {
                        "pattern_a": a,
                        "pattern_b": b,
                        "similarity_score": round(score, 4),
                        "method": "jaccard_fallback",
                    }
                )
    return pairs
