"""STIL parser strategy adapter for FA-FR-001 enterprise ingestion."""

from __future__ import annotations

from pathlib import Path

from parser_engine.adapters.schema import TestRecord
from parser_engine.parsers.base import BaseParser, ParserResult
from parser_engine.parsers.stil.stil_ingestor import ingest_stil_file


class StilParser(BaseParser):
    """Wraps streaming stil_ingestor into the BaseParser Strategy interface."""

    parser_id = "stil_v1"

    def supported_extensions(self) -> set[str]:
        return {".stil"}

    def detect(self, path: Path) -> bool:
        if path.suffix.lower() != ".stil":
            return False
        try:
            with path.open("r", encoding="utf-8", errors="replace") as handle:
                head = handle.read(2048)
            return "STIL" in head or "ScanStructures" in head or "PatternBurst" in head
        except OSError:
            return False

    def parse(self, path: Path) -> ParserResult:
        try:
            stil = ingest_stil_file(path)
        except Exception as exc:  # noqa: BLE001
            return ParserResult(errors=[{"file": str(path), "error": str(exc)}])

        errors: list[dict[str, str]] = [{"file": str(path), "error": e} for e in stil.errors]
        if not stil.validation_passed:
            errors.append(
                {
                    "file": str(path),
                    "error": "STIL validation failed — missing scan chains or patterns",
                }
            )

        records: list[TestRecord] = []
        # Persist one canonical summary record so the dataset has a durable identity
        # in normalized_records while rich metadata lives in parser_metadata.
        meta = stil.metadata
        summary = TestRecord(
            lot_id=meta.source or "STIL_LIBRARY",
            wafer_id=meta.test_set_type or "SCAN",
            die_id=f"STIL_{path.stem}",
            test_stage="STIL",
            tester_id=meta.source or "ATE",
            pass_fail="PASS" if stil.validation_passed else "FAIL",
            timestamp=meta.date or "",
            source_file=str(path),
            adapter_id=self.parser_id,
            product_id=meta.title or path.stem,
            failing_patterns=[],
            scan_fail_data={
                "pattern_begin": meta.pattern_begin,
                "pattern_end": meta.pattern_end,
                "pattern_count": stil.pattern_count_verified,
                "scan_chain_count": len(stil.scan_chains),
            },
            parametric={
                "total_patterns": float(stil.pattern_count_verified),
                "scan_chains": float(len(stil.scan_chains)),
            },
            raw_fields={
                "format_version": meta.format_version,
                "tcd_signature": meta.tcd_signature,
            },
        )
        summary.record_key = summary.build_record_key()
        records.append(summary)

        # Optional per-chain rows for downstream pattern correlation
        for chain in stil.scan_chains[:500]:
            row = TestRecord(
                lot_id=summary.lot_id,
                wafer_id=summary.wafer_id,
                die_id=chain.chain_id,
                test_stage="STIL_SCAN_CHAIN",
                tester_id=summary.tester_id,
                pass_fail="INFO",
                timestamp=summary.timestamp,
                source_file=str(path),
                adapter_id=self.parser_id,
                scan_fail_data=chain.to_dict(),
                parametric={"scan_length": float(chain.scan_length or 0)},
            )
            row.record_key = row.build_record_key()
            records.append(row)

        return ParserResult(
            records=records,
            errors=errors,
            metadata={
                "stil": {
                    "title": meta.title,
                    "date": meta.date,
                    "source": meta.source,
                    "test_set_type": meta.test_set_type,
                    "pattern_begin": meta.pattern_begin,
                    "pattern_end": meta.pattern_end,
                    "total_patterns": meta.total_patterns,
                    "pattern_count_verified": stil.pattern_count_verified,
                    "validation_passed": stil.validation_passed,
                    "validation_notes": stil.validation_notes,
                    "scan_chains": [c.to_dict() for c in stil.scan_chains],
                    "file_size_bytes": stil.file_size_bytes,
                }
            },
        )
