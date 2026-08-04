"""File / outcome metadata enrichment."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from parser_engine.v2.contracts import ParseOutcome


class MetadataService:
    def file_info(self, path: Path) -> dict[str, Any]:
        try:
            st = path.stat()
            return {
                "path": str(path.resolve()),
                "name": path.name,
                "suffix": path.suffix.lower(),
                "size_bytes": st.st_size,
                "mtime": st.st_mtime,
                "ctime": st.st_ctime,
            }
        except OSError as exc:
            return {"path": str(path), "error": str(exc)}

    def enrich(self, path: Path, outcome: ParseOutcome) -> dict[str, Any]:
        meta = dict(outcome.metadata)
        meta["file"] = self.file_info(path)
        meta["pid"] = os.getpid()
        meta["record_count"] = len(outcome.records)
        meta["error_count"] = len(outcome.errors)
        meta["quarantine_count"] = len(outcome.quarantine)
        meta["parser_id"] = outcome.parser_id
        return meta
