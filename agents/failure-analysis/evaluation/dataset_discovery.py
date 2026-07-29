"""Dataset discovery and STIL↔log matching (no hardcoded filenames)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

from adapters.yaml_config import load_adapter_configs
from evaluation.domain import DatasetBundle, DiscoveredInventory

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "evaluation.yaml"
PROJECT_ROOT = Path(__file__).resolve().parents[1]

DATA_EXTENSIONS = {".stil", ".log", ".txt", ".csv", ".json"}


class DatasetDiscoveryEngine:
    """
    Recursively scan configured roots for semiconductor datasets and
    automatically pair STIL files with matching generated log corpora.
    """

    def __init__(self, *, config_path: Path | str | None = None) -> None:
        self.config = load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
        self.search_roots = self._resolve_roots()
        self.scale_tokens = [
            str(t).lower() for t in self.config.get("matching", {}).get("scale_tokens", [])
        ]
        self.labelled_patterns = [
            str(p).lower()
            for p in self.config.get("matching", {}).get("labelled_name_patterns", [])
        ]
        self.ignore_patterns = [
            str(p).lower()
            for p in self.config.get("matching", {}).get("ignore_name_patterns", [])
        ]
        self.prefer_labelled = bool(
            self.config.get("matching", {}).get("prefer_labelled_logs", True)
        )

    def discover(self) -> DiscoveredInventory:
        stil_files: list[Path] = []
        log_files: list[Path] = []
        tabular_files: list[Path] = []
        warnings: list[str] = []

        for root in self.search_roots:
            if not root.is_dir():
                warnings.append(f"Search root not found (skipped): {root}")
                continue
            for path in root.rglob("*"):
                if not path.is_file():
                    continue
                suffix = path.suffix.lower()
                if suffix not in DATA_EXTENSIONS:
                    continue
                if self._should_ignore(path):
                    continue
                if suffix == ".stil":
                    stil_files.append(path)
                elif suffix in {".log", ".txt"} and self._looks_like_tester_log(path):
                    log_files.append(path)
                elif suffix in {".csv", ".json"}:
                    tabular_files.append(path)

        stil_files = sorted(set(stil_files))
        log_files = sorted(set(log_files))
        tabular_files = sorted(set(tabular_files))

        bundles = self._match_bundles(stil_files, log_files, tabular_files, warnings)
        return DiscoveredInventory(
            roots=[str(r) for r in self.search_roots],
            stil_files=stil_files,
            log_files=log_files,
            tabular_files=tabular_files,
            bundles=bundles,
            warnings=warnings,
        )

    def _resolve_roots(self) -> list[Path]:
        from evaluation.data_roots import candidate_verilumen_roots

        env = os.getenv("EVALUATION_DATA_ROOTS", "").strip()
        raw_roots: list[str]
        if env:
            raw_roots = [p.strip() for p in env.split(";") if p.strip()]
        else:
            raw_roots = list(self.config.get("search_roots", ["."]))

        resolved: list[Path] = []
        for item in raw_roots:
            path = Path(item).expanduser()
            if not path.is_absolute():
                path = (PROJECT_ROOT / path).resolve()
            else:
                path = path.resolve()
            if path not in resolved:
                resolved.append(path)

        # Auto-discover Verilumen Labs under the user home / DATASET_ROOT (no hardcoded users).
        for path in candidate_verilumen_roots():
            if path.is_dir() and path not in resolved:
                resolved.insert(0, path)
        return resolved

    def _should_ignore(self, path: Path) -> bool:
        name = path.name.lower()
        parts = {p.lower() for p in path.parts}
        if "node_modules" in parts or ".git" in parts or "__pycache__" in parts:
            return True
        if "storage" in parts and "raw" in parts:
            return True
        return any(token in name for token in self.ignore_patterns)

    def _looks_like_tester_log(self, path: Path) -> bool:
        name = path.name.lower()
        if path.suffix.lower() == ".log":
            return True
        # .txt may be docs; keep files that look like ATE logs
        return any(
            token in name
            for token in ("log_", "fail_die", "good_die", "ate", "tester", "datalog")
        )

    def _match_bundles(
        self,
        stil_files: list[Path],
        log_files: list[Path],
        tabular_files: list[Path],
        warnings: list[str],
    ) -> list[DatasetBundle]:
        bundles: list[DatasetBundle] = []
        used_stils: set[Path] = set()
        used_logs: set[Path] = set()

        for token in self.scale_tokens:
            stil_matches = [p for p in stil_files if token in p.name.lower()]
            log_matches = [
                p for p in log_files if self._path_matches_scale(p, token)
            ]
            if not stil_matches and not log_matches:
                continue

            labelled = [p for p in log_matches if self._is_labelled_log(p)]
            if self.prefer_labelled and labelled:
                preferred = labelled
            else:
                preferred = log_matches

            bundle_warnings: list[str] = []
            if stil_matches and not log_matches:
                bundle_warnings.append(
                    f"STIL scale '{token}' found but matching logs unavailable; continuing."
                )
                warnings.extend(bundle_warnings)
            if log_matches and not stil_matches:
                bundle_warnings.append(
                    f"Logs for scale '{token}' found but matching STIL unavailable; continuing."
                )
                warnings.extend(bundle_warnings)

            tabular = [
                p
                for p in tabular_files
                if token in str(p).lower() or "dashboard_data" in str(p).lower()
            ]

            dataset_id = f"scale_{token}"
            if stil_matches:
                dataset_id = stil_matches[0].stem

            bundles.append(
                DatasetBundle(
                    dataset_id=dataset_id,
                    scale_token=token,
                    stil_paths=stil_matches,
                    log_paths=log_matches,
                    labelled_log_paths=labelled,
                    tabular_paths=tabular,
                    warnings=bundle_warnings,
                    metadata={
                        "preferred_log_count": len(preferred),
                        "stil_names": [p.name for p in stil_matches],
                    },
                )
            )
            used_stils.update(stil_matches)
            used_logs.update(log_matches)

        orphan_stils = [p for p in stil_files if p not in used_stils]
        orphan_logs = [p for p in log_files if p not in used_logs]
        if orphan_stils or orphan_logs:
            warnings.append(
                f"Unmatched assets: {len(orphan_stils)} STIL, {len(orphan_logs)} logs "
                "(retained as unmatched bundle)."
            )
            bundles.append(
                DatasetBundle(
                    dataset_id="unmatched",
                    scale_token="unmatched",
                    stil_paths=orphan_stils,
                    log_paths=orphan_logs,
                    labelled_log_paths=[p for p in orphan_logs if self._is_labelled_log(p)],
                    tabular_paths=[],
                    warnings=["Assets that did not match a known scale token."],
                    metadata={},
                )
            )

        return bundles

    def _path_matches_scale(self, path: Path, token: str) -> bool:
        haystack = str(path).lower().replace("\\", "/")
        if token in {"full", "29642", "29625"}:
            # Full-scale logs may live under folders without "full" in the name
            # (e.g. log_XX with TOTAL_PATTERNS ~29625). Match parent folder tokens
            # or explicit full markers.
            if any(t in haystack for t in ("full", "29642", "29625")):
                return True
            # Do not claim every log as full; only when no 1000/2000 folder marker
            if "1000" in haystack or "2000" in haystack:
                return False
            return "generated_logs" in haystack and token == "full"
        return token in haystack

    def _is_labelled_log(self, path: Path) -> bool:
        name = path.name.lower()
        return any(pat in name for pat in self.labelled_patterns)


def load_evaluation_config(config_path: Path | str | None = None) -> dict[str, Any]:
    return load_adapter_configs(Path(config_path) if config_path else DEFAULT_CONFIG)
