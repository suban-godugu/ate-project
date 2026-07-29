"""FA-FR-005 semantic correctness tests over FA-FR-004 classified faults."""

from __future__ import annotations

import random
import unittest

from backend.recurring.production_engine import ProductionRecurrenceEngine
from backend.recurring.production_service import recurrence_benchmarks
from tests.test_fa_fr_004_recurrence import observation


class FaFr005SemanticTests(unittest.TestCase):
    def test_same_pattern_with_different_fault_types_does_not_merge(self) -> None:
        rows = []
        for fault_type in ("Scan Chain Failure", "Timing Failure"):
            for execution, source in (("old", "LOT1"), ("new", "LOT2")):
                row = observation(0, execution=execution, source=source)
                row["fault_type"] = fault_type
                rows.append(row)
        result = ProductionRecurrenceEngine().analyze(
            observations=rows,
            current_execution_id="new",
            source_record_counts={"old": 10, "new": 10},
            failure_rates={"P2001": 10.0},
            incremental=True,
        )
        self.assertEqual(
            {item["fault_type"] for item in result["recurrences"]},
            {"Scan Chain Failure", "Timing Failure"},
        )
        self.assertEqual(
            len(
                {
                    item["canonical_recurrence_key"]
                    for item in result["recurrences"]
                }
            ),
            2,
        )

    def test_similarity_and_hotspots_are_order_deterministic(self) -> None:
        rows = []
        for pattern in ("P1", "P2", "P3"):
            for execution, source in (("old", "LOT1"), ("new", "LOT2")):
                rows.append(
                    observation(
                        0,
                        execution=execution,
                        source=source,
                        pattern=pattern,
                    )
                )
        shuffled = list(rows)
        random.Random(42).shuffle(shuffled)
        kwargs = {
            "current_execution_id": "new",
            "source_record_counts": {"old": 10, "new": 10},
            "failure_rates": {"P1": 10.0, "P2": 10.0, "P3": 10.0},
            "incremental": True,
        }
        first = ProductionRecurrenceEngine().analyze(observations=rows, **kwargs)
        second = ProductionRecurrenceEngine().analyze(observations=shuffled, **kwargs)
        first_groups = {
            item["canonical_recurrence_key"]: item["similarity_group"]
            for item in first["recurrences"]
        }
        second_groups = {
            item["canonical_recurrence_key"]: item["similarity_group"]
            for item in second["recurrences"]
        }
        self.assertEqual(first_groups, second_groups)
        self.assertEqual(
            sorted(
                (item["pattern_id"], item["x"], item["y"], item["occurrence_count"])
                for item in first["hotspots"]
            ),
            sorted(
                (item["pattern_id"], item["x"], item["y"], item["occurrence_count"])
                for item in second["hotspots"]
            ),
        )

    def test_benchmark_uses_known_negatives_for_false_positive_rate(self) -> None:
        metrics = recurrence_benchmarks(
            [{"pattern_id": "P1"}, {"pattern_id": "N1"}],
            ["P1"],
            ["N1", "N2"],
        )
        self.assertEqual(metrics["precision"], 0.5)
        self.assertEqual(metrics["recall"], 1.0)
        self.assertEqual(metrics["false_positive_rate"], 0.5)
        self.assertEqual(metrics["false_negative_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
