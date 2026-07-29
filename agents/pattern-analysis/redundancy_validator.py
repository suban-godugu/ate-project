"""
PA-FR-007 Redundancy Validator — automated checks on redundancy candidates.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from redundancy_engine import RedundancyCandidate, RedundancyConfig, RedundancyRunResult, candidate_sort_key


def _overall_status(checks: List[Dict[str, Any]]) -> str:
    if any(check["status"] == "FAIL" for check in checks):
        return "FAIL"
    if any(check["status"] == "WARNING" for check in checks):
        return "WARNING"
    return "PASS"


def validate_redundancy_result(
    result: RedundancyRunResult,
    config: RedundancyConfig,
    audit_entries: Sequence[Dict[str, Any]] | None = None,
    manifest_generated: bool = False,
) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []
    candidates = result.candidates

    if result.embedding_version:
        checks.append(
            {
                "rule": "embedding_version_exists",
                "status": "PASS",
                "details": f"Embedding version {result.embedding_version} is present.",
            }
        )
    else:
        checks.append(
            {
                "rule": "embedding_version_exists",
                "status": "FAIL",
                "details": "Embedding version is missing.",
            }
        )

    missing_cluster_ids = [
        candidate
        for candidate in candidates
        if not candidate.cluster_id
    ]
    if not missing_cluster_ids:
        checks.append(
            {
                "rule": "cluster_ids_exist",
                "status": "PASS",
                "details": f"Checked {len(candidates)} candidates, all cluster IDs present.",
            }
        )
    else:
        checks.append(
            {
                "rule": "cluster_ids_exist",
                "status": "FAIL",
                "details": f"Found {len(missing_cluster_ids)} candidate(s) without cluster IDs.",
            }
        )

    missing_pattern_ids = [
        candidate
        for candidate in candidates
        if not candidate.pattern_a or not candidate.pattern_b
    ]
    if not missing_pattern_ids:
        checks.append(
            {
                "rule": "pattern_ids_exist",
                "status": "PASS",
                "details": f"Checked {len(candidates)} candidates, all pattern IDs present.",
            }
        )
    else:
        checks.append(
            {
                "rule": "pattern_ids_exist",
                "status": "FAIL",
                "details": f"Found {len(missing_pattern_ids)} candidate(s) with empty pattern IDs.",
            }
        )

    self_comparisons = [
        candidate
        for candidate in candidates
        if candidate.pattern_a == candidate.pattern_b
    ]
    if not self_comparisons:
        checks.append(
            {
                "rule": "no_self_comparisons",
                "status": "PASS",
                "details": f"Checked {len(candidates)} candidates, 0 self-comparisons found.",
            }
        )
    else:
        checks.append(
            {
                "rule": "no_self_comparisons",
                "status": "FAIL",
                "details": f"Found {len(self_comparisons)} self-comparison candidate(s).",
            }
        )

    pair_keys = [(candidate.pattern_a, candidate.pattern_b) for candidate in candidates]
    if len(pair_keys) == len(set(pair_keys)):
        checks.append(
            {
                "rule": "no_duplicate_candidate_pairs",
                "status": "PASS",
                "details": f"Checked {len(candidates)} candidates, 0 duplicate pairs found.",
            }
        )
    else:
        checks.append(
            {
                "rule": "no_duplicate_candidate_pairs",
                "status": "FAIL",
                "details": f"Found {len(pair_keys) - len(set(pair_keys))} duplicate candidate pair(s).",
            }
        )

    below_threshold = [
        candidate
        for candidate in candidates
        if candidate.raw_similarity < config.similarity_threshold
    ]
    if not below_threshold:
        checks.append(
            {
                "rule": "similarity_threshold_respected",
                "status": "PASS",
                "details": (
                    f"Checked {len(candidates)} candidates against threshold "
                    f"{config.similarity_threshold}."
                ),
            }
        )
    else:
        checks.append(
            {
                "rule": "similarity_threshold_respected",
                "status": "FAIL",
                "details": f"Found {len(below_threshold)} candidate(s) below threshold.",
            }
        )

    max_confidence = config.embedding_only_confidence_weight
    invalid_confidence = [
        candidate
        for candidate in candidates
        if candidate.confidence_score < 0.0 or candidate.confidence_score > max_confidence
    ]
    if not invalid_confidence:
        checks.append(
            {
                "rule": "confidence_within_valid_range",
                "status": "PASS",
                "details": (
                    f"All confidence scores within 0.0 and {max_confidence} "
                    f"for Embedding-Only mode."
                ),
            }
        )
    else:
        checks.append(
            {
                "rule": "confidence_within_valid_range",
                "status": "FAIL",
                "details": f"Found {len(invalid_confidence)} candidate(s) outside valid confidence range.",
            }
        )

    missing_source = [
        candidate for candidate in candidates if candidate.confidence_source != config.confidence_source
    ]
    if not missing_source:
        checks.append(
            {
                "rule": "confidence_source_populated",
                "status": "PASS",
                "details": f'All candidates use confidence_source "{config.confidence_source}".',
            }
        )
    else:
        checks.append(
            {
                "rule": "confidence_source_populated",
                "status": "FAIL",
                "details": f"Found {len(missing_source)} candidate(s) with unexpected confidence_source.",
            }
        )

    missing_review = [
        candidate for candidate in candidates if candidate.review_status != config.review_status
    ]
    if not missing_review:
        checks.append(
            {
                "rule": "review_status_populated",
                "status": "PASS",
                "details": f'All candidates use review_status "{config.review_status}".',
            }
        )
    else:
        checks.append(
            {
                "rule": "review_status_populated",
                "status": "FAIL",
                "details": f"Found {len(missing_review)} candidate(s) with unexpected review_status.",
            }
        )

    resorted = sorted(candidates, key=candidate_sort_key)
    ordering_matches = all(
        left.pattern_a == right.pattern_a and left.pattern_b == right.pattern_b
        for left, right in zip(candidates, resorted)
    )
    if ordering_matches:
        checks.append(
            {
                "rule": "candidate_ordering_deterministic",
                "status": "PASS",
                "details": "Candidate ordering matches deterministic four-level sort.",
            }
        )
    else:
        checks.append(
            {
                "rule": "candidate_ordering_deterministic",
                "status": "FAIL",
                "details": "Candidate ordering is not deterministic.",
            }
        )

    audit_entries = list(audit_entries or [])
    if audit_entries and len(audit_entries) == len(candidates):
        checks.append(
            {
                "rule": "audit_log_generated",
                "status": "PASS",
                "details": f"Audit log contains {len(audit_entries)} exported candidate entries.",
            }
        )
    elif not candidates and not audit_entries:
        checks.append(
            {
                "rule": "audit_log_generated",
                "status": "PASS",
                "details": "No exported candidates; audit log is empty.",
            }
        )
    else:
        checks.append(
            {
                "rule": "audit_log_generated",
                "status": "FAIL",
                "details": (
                    f"Audit log entry count ({len(audit_entries)}) does not match "
                    f"candidate count ({len(candidates)})."
                ),
            }
        )

    if manifest_generated:
        checks.append(
            {
                "rule": "manifest_generated",
                "status": "PASS",
                "details": "Redundancy manifest generated.",
            }
        )
    else:
        checks.append(
            {
                "rule": "manifest_generated",
                "status": "FAIL",
                "details": "Redundancy manifest was not generated.",
            }
        )

    if result.duplicate_pattern_ids:
        checks.append(
            {
                "rule": "duplicate_pattern_ids",
                "status": "WARNING",
                "details": (
                    f"Duplicate pattern IDs detected in input: "
                    f"{', '.join(sorted(set(result.duplicate_pattern_ids)))}"
                ),
            }
        )

    passed = sum(1 for check in checks if check["status"] == "PASS")
    warnings = sum(1 for check in checks if check["status"] == "WARNING")
    failed = sum(1 for check in checks if check["status"] == "FAIL")
    return {
        "generated_by": "PA-FR-007",
        "validation_status": _overall_status(checks),
        "total_checks": len(checks),
        "passed": passed,
        "warnings": warnings,
        "failed": failed,
        "checks": checks,
    }
