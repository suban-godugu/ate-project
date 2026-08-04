"""Content-fingerprint cache manager for v2 parse outcomes."""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from parser_engine.v2.contracts import ParseOutcome
from parser_engine.v2.models.enterprise_record import EnterpriseRecord


class CacheManager:
    """Disk JSON cache keyed by path+mtime+size+parser_id+version."""

    VERSION = "2.0.0"

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or (Path.home() / ".cache" / "parser_engine_v2")
        self.root.mkdir(parents=True, exist_ok=True)
        self._hits = 0
        self._misses = 0

    def fingerprint(self, path: Path, parser_id: str, profile: str = "auto") -> str:
        try:
            st = path.stat()
            payload = f"{path.resolve()}|{st.st_mtime_ns}|{st.st_size}|{parser_id}|{profile}|{self.VERSION}"
        except OSError:
            payload = f"{path}|{parser_id}|{profile}|{self.VERSION}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def _path_for(self, key: str) -> Path:
        return self.root / f"{key}.json"

    def get(self, path: Path, parser_id: str, profile: str = "auto") -> ParseOutcome | None:
        key = self.fingerprint(path, parser_id, profile)
        cache_path = self._path_for(key)
        if not cache_path.exists():
            self._misses += 1
            return None
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            records = [EnterpriseRecord.from_dict(r) for r in data.get("records", [])]
            outcome = ParseOutcome(
                parser_id=data.get("parser_id", parser_id),
                records=records,
                metadata=dict(data.get("metadata") or {}),
                success=bool(data.get("success", True)),
                cache_hit=True,
            )
            self._hits += 1
            return outcome
        except Exception:
            self._misses += 1
            return None

    def put(self, path: Path, parser_id: str, outcome: ParseOutcome, profile: str = "auto") -> None:
        key = self.fingerprint(path, parser_id, profile)
        payload: dict[str, Any] = {
            "parser_id": outcome.parser_id,
            "success": outcome.success,
            "metadata": outcome.metadata,
            "records": [r.to_dict() for r in outcome.records],
            "cached_at": time.time(),
        }
        try:
            self._path_for(key).write_text(json.dumps(payload, default=str), encoding="utf-8")
        except OSError:
            pass

    def stats(self) -> dict[str, int]:
        return {"hits": self._hits, "misses": self._misses}
