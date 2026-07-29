"""
PA-ARCH-003 — On-demand Analysis Session artifact catalog.

Preflight SHA256 without loading JSON bodies; load one artifact at a time.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from engineering_data_exchange import (
    CORE_ARTIFACTS,
    OPTIONAL_ARTIFACTS,
    file_sha256,
)


class ArtifactCatalog:
    """Load session artifacts one at a time; track preflight provenance."""

    def __init__(self, output_dir: str) -> None:
        self.output_dir = output_dir
        self.provenance: Dict[str, Dict[str, Any]] = {}
        self.warnings: List[str] = []
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}

    def preflight(self) -> None:
        """Hash each allowlisted file and record provenance without json.load."""
        self.provenance.clear()
        self.warnings.clear()
        for logical_name, filename in CORE_ARTIFACTS:
            self._preflight_one(logical_name, filename, required=True)
        for logical_name, filename in OPTIONAL_ARTIFACTS:
            self._preflight_one(logical_name, filename, required=False)

    def _preflight_one(
        self,
        logical_name: str,
        filename: str,
        *,
        required: bool,
    ) -> None:
        if filename.startswith("PA-FR-"):
            raise ValueError(f"PA-FR-* artifacts are forbidden: {filename}")

        path = os.path.join(self.output_dir, filename)
        record: Dict[str, Any] = {
            "logical_name": logical_name,
            "artifact_filename": filename,
            "status": "Missing",
            "sha256": None,
            "generated_by": None,
        }
        if not os.path.exists(path):
            if required:
                self.warnings.append(f"Missing artifact: {filename}")
            self.provenance[logical_name] = record
            return

        try:
            digest = file_sha256(path)
        except OSError as exc:
            if required:
                self.warnings.append(f"Unreadable artifact {filename}: {exc}")
            self.provenance[logical_name] = record
            return

        generated_by = None
        try:
            with open(path, "r", encoding="utf-8") as handle:
                prefix = handle.read(4096)
            if '"generated_by"' in prefix:
                import re

                match = re.search(r'"generated_by"\s*:\s*"([^"]*)"', prefix)
                if match:
                    generated_by = match.group(1)
        except OSError:
            pass

        record.update(
            {
                "status": "Complete",
                "sha256": digest,
                "generated_by": generated_by,
            }
        )
        self.provenance[logical_name] = record

    def load(self, logical_name: str) -> Optional[Dict[str, Any]]:
        """Load one artifact JSON body; cached until release()."""
        if logical_name in self._cache:
            return self._cache[logical_name]

        filename = self._filename_for(logical_name)
        if filename is None:
            return None

        path = os.path.join(self.output_dir, filename)
        record = self.provenance.get(logical_name) or {}
        if record.get("status") != "Complete":
            self._cache[logical_name] = None
            return None

        try:
            with open(path, "r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError):
            self._cache[logical_name] = None
            return None

        if not isinstance(payload, dict):
            self._cache[logical_name] = None
            return None

        if record.get("generated_by") is None and payload.get("generated_by") is not None:
            record["generated_by"] = payload.get("generated_by")

        self._cache[logical_name] = payload
        return payload

    def release(self, logical_name: str) -> None:
        """Drop cached artifact payload to bound memory."""
        self._cache.pop(logical_name, None)

    def release_all(self) -> None:
        self._cache.clear()

    def load_many(self, logical_names: List[str]) -> Dict[str, Optional[Dict[str, Any]]]:
        return {name: self.load(name) for name in logical_names}

    def release_many(self, logical_names: List[str]) -> None:
        for name in logical_names:
            self.release(name)

    def artifacts_view(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """Shallow view of currently cached artifacts for build_* helpers."""
        return dict(self._cache)

    @staticmethod
    def _filename_for(logical_name: str) -> Optional[str]:
        for name, filename in list(CORE_ARTIFACTS) + list(OPTIONAL_ARTIFACTS):
            if name == logical_name:
                return filename
        return None
