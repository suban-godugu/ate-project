"""Semantic retrieval engine for similar historical failures (RAG)."""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs

logger = logging.getLogger(__name__)

DEFAULT_KB = Path(__file__).resolve().parents[2] / "config" / "root_cause_knowledge.yaml"


class RAGEngine:
    """
    Retrieve similar historical failure cases via semantic search.
    Uses sentence-transformers + FAISS when available; falls back to TF-IDF.
    """

    def __init__(
        self,
        *,
        knowledge_base_path: Path | str | None = None,
        top_k: int = 5,
        similarity_threshold: float = 0.35,
        embedding_model: str = "all-MiniLM-L6-v2",
        use_faiss: bool = True,
    ) -> None:
        self.top_k = top_k
        self.similarity_threshold = similarity_threshold
        self.embedding_model = embedding_model
        self.use_faiss = use_faiss
        kb_path = Path(knowledge_base_path) if knowledge_base_path else DEFAULT_KB
        self.cases = _load_cases(kb_path)
        self._index = _build_index(self.cases, embedding_model, use_faiss)

    def search(
        self,
        query: str,
        *,
        top_k: int | None = None,
    ) -> tuple[list[dict[str, Any]], float]:
        start = time.perf_counter()
        k = top_k or self.top_k
        results = self._index.search(query, k=k, threshold=self.similarity_threshold)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        return results, elapsed_ms

    def search_for_context(self, ctx: dict[str, Any]) -> tuple[list[dict[str, Any]], float]:
        query = ctx.get("semantic_query", "")
        if ctx.get("primary_hint"):
            query += " " + ctx["primary_hint"]
        if ctx.get("primary_fault_category"):
            query += " " + ctx["primary_fault_category"]
        return self.search(query)


def _load_cases(path: Path) -> list[dict[str, Any]]:
    raw = load_adapter_configs(path)
    cases = raw.get("historical_cases", [])
    for case in cases:
        keywords = case.get("keywords", [])
        case["document"] = " ".join(
            [
                str(case.get("fault_type", "")),
                str(case.get("root_cause", "")),
                str(case.get("investigation", "")),
                " ".join(str(k) for k in keywords),
            ]
        )
    return cases


class _SemanticIndex:
    def search(self, query: str, *, k: int, threshold: float) -> list[dict[str, Any]]:
        raise NotImplementedError


class _TfidfIndex(_SemanticIndex):
    def __init__(self, cases: list[dict[str, Any]]) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self.cases = cases
        self._cosine_similarity = cosine_similarity
        docs = [c["document"] for c in cases]
        self._vectorizer = TfidfVectorizer(stop_words="english")
        self._matrix = self._vectorizer.fit_transform(docs)

    def search(self, query: str, *, k: int, threshold: float) -> list[dict[str, Any]]:
        query_vec = self._vectorizer.transform([query])
        scores = self._cosine_similarity(query_vec, self._matrix)[0]
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:k]
        results: list[dict[str, Any]] = []
        for idx, score in ranked:
            if float(score) < threshold:
                continue
            case = dict(self.cases[idx])
            case["similarity_score"] = round(float(score), 4)
            results.append(case)
        return results


class _EmbeddingFaissIndex(_SemanticIndex):
    def __init__(self, cases: list[dict[str, Any]], model_name: str) -> None:
        import numpy as np
        from sentence_transformers import SentenceTransformer

        self.cases = cases
        self._np = np
        model = SentenceTransformer(model_name)
        docs = [c["document"] for c in cases]
        embeddings = model.encode(docs, normalize_embeddings=True)
        self._embeddings = np.array(embeddings, dtype=np.float32)

        try:
            import faiss

            dim = self._embeddings.shape[1]
            index = faiss.IndexFlatIP(dim)
            index.add(self._embeddings)
            self._faiss = index
            self._use_faiss = True
        except ImportError:
            self._faiss = None
            self._use_faiss = False

        self._model = model

    def search(self, query: str, *, k: int, threshold: float) -> list[dict[str, Any]]:
        query_vec = self._model.encode([query], normalize_embeddings=True)
        query_vec = self._np.array(query_vec, dtype=self._np.float32)

        if self._use_faiss and self._faiss is not None:
            scores, indices = self._faiss.search(query_vec, k)
            pairs = list(zip(indices[0], scores[0]))
        else:
            scores = (self._embeddings @ query_vec.T).flatten()
            indices = scores.argsort()[::-1][:k]
            pairs = [(int(i), float(scores[i])) for i in indices]

        results: list[dict[str, Any]] = []
        for idx, score in pairs:
            if idx < 0 or float(score) < threshold:
                continue
            case = dict(self.cases[idx])
            case["similarity_score"] = round(float(score), 4)
            results.append(case)
        return results


def _build_index(
    cases: list[dict[str, Any]],
    embedding_model: str,
    use_faiss: bool,
) -> _SemanticIndex:
    if not cases:
        return _TfidfIndex([{"document": "placeholder", "case_id": "EMPTY"}])

    if use_faiss:
        try:
            return _EmbeddingFaissIndex(cases, embedding_model)
        except Exception as exc:
            logger.info("Embedding/FAISS index unavailable (%s); using TF-IDF", exc)

    return _TfidfIndex(cases)
