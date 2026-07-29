"""
PA-FR-007 Redundancy Audit — audit log for exported redundancy candidates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from redundancy_engine import RedundancyCandidate, RedundancyConfig


def build_redundancy_audit_entries(
    candidates: Sequence[RedundancyCandidate],
    config: RedundancyConfig,
    generated_timestamp: str,
) -> List[Dict[str, Any]]:
    if not config.enable_audit_logging:
        return []
    return [
        {
            "pattern_a": candidate.pattern_a,
            "pattern_b": candidate.pattern_b,
            "cluster_id": candidate.cluster_id,
            "raw_similarity": candidate.raw_similarity,
            "confidence_score": candidate.confidence_score,
            "confidence_source": candidate.confidence_source,
            "similarity_threshold": config.similarity_threshold,
            "timestamp": generated_timestamp,
            "review_status": candidate.review_status,
        }
        for candidate in candidates
    ]
