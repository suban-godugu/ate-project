"""Deterministic AI-oriented feature extraction (no LLM dependency)."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any

from parser_engine.v2.contracts import ParseOutcome
from parser_engine.v2.models.enterprise_record import EnterpriseRecord


class AIFeatureService:
    def failure_signature_hash(self, record: EnterpriseRecord) -> str:
        payload = "|".join(
            [
                record.chain_id,
                record.fail_flop_id,
                record.fail_type,
                record.expected_signature[:64],
                record.actual_signature[:64],
                ",".join(sorted(record.failing_patterns[:5])),
            ]
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    def pattern_fail_counts(self, records: list[EnterpriseRecord]) -> dict[str, int]:
        c: Counter[str] = Counter()
        for r in records:
            for p in r.failing_patterns:
                c[p] += 1
            if r.chain_id and r.pass_fail.upper() == "FAIL":
                c[f"chain:{r.chain_id}"] += 1
        return dict(c)

    def yield_metrics(self, records: list[EnterpriseRecord], *, die_population: int | None = None) -> dict[str, float]:
        if not records:
            return {"fail_count": 0.0, "pass_count": 0.0, "yield": 0.0}
        fails = sum(1 for r in records if str(r.pass_fail).upper() == "FAIL")
        passes = sum(1 for r in records if str(r.pass_fail).upper() == "PASS")
        denom = die_population if die_population and die_population > 0 else max(fails + passes, 1)
        return {
            "fail_count": float(fails),
            "pass_count": float(passes),
            "yield": float(passes) / float(denom),
        }

    def feature_vector(self, records: list[EnterpriseRecord]) -> dict[str, float]:
        fails = sum(1 for r in records if str(r.pass_fail).upper() == "FAIL")
        chains = {r.chain_id for r in records if r.chain_id}
        patterns = {p for r in records for p in r.failing_patterns}
        conf = [r.parse_confidence for r in records]
        return {
            "n_records": float(len(records)),
            "n_fails": float(fails),
            "n_chains": float(len(chains)),
            "n_patterns": float(len(patterns)),
            "avg_confidence": float(sum(conf) / len(conf)) if conf else 0.0,
            "quarantine_rate": float(sum(1 for r in records if r.is_quarantined()) / len(records))
            if records
            else 0.0,
        }

    def from_outcome(self, outcome: ParseOutcome, *, die_population: int | None = None) -> dict[str, Any]:
        records = outcome.records
        sigs = [self.failure_signature_hash(r) for r in records[:50]]
        return {
            "parser_id": outcome.parser_id,
            "pattern_fail_counts": self.pattern_fail_counts(records),
            "yield": self.yield_metrics(records, die_population=die_population),
            "features": self.feature_vector(records),
            "signature_samples": sigs,
            "quality": {
                "error_count": len(outcome.errors),
                "quarantine_count": len(outcome.quarantine),
                "success": outcome.success,
            },
        }
