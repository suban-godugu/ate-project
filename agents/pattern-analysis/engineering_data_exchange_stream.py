"""
PA-ARCH-003 — Streaming JSON writer for pattern_analysis_master.json.

Emits byte-identical output to json.dump(..., indent=2, sort_keys=True, ensure_ascii=False)
without materializing the full master dict in memory.
"""
from __future__ import annotations

import json
import os
from typing import Any, IO, List, Optional, Tuple


def _format_root_entry(key: str, value: Any) -> List[str]:
    """Format one top-level key/value pair matching json.dump indent=2."""
    blob = json.dumps(
        {key: value},
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    )
    lines = blob.splitlines()
    if len(lines) < 2:
        return [f'  "{key}": {json.dumps(value, ensure_ascii=False)}']
    return lines[1:-1]


class StreamingJsonWriter:
  """Incrementally write a JSON object to disk with deterministic formatting."""

  def __init__(self, output_dir: str, filename: str) -> None:
      self.output_dir = output_dir
      self.filename = filename
      self._tmp_path = os.path.join(output_dir, f"{filename}.tmp")
      self._final_path = os.path.join(output_dir, filename)
      self._handle: Optional[IO[str]] = None
      self._entry_count = 0

  @property
  def final_path(self) -> str:
      return self._final_path

  def open(self) -> None:
      os.makedirs(self.output_dir, exist_ok=True)
      self._handle = open(self._tmp_path, "w", encoding="utf-8", newline="\n")
      self._handle.write("{\n")
      self._entry_count = 0
      self._buffered_entry: Optional[List[str]] = None

  def write_entry(self, key: str, value: Any) -> None:
      if self._handle is None:
          raise RuntimeError("StreamingJsonWriter is not open")
      lines = _format_root_entry(key, value)
      if self._buffered_entry is not None:
          self._buffered_entry[-1] += ","
          self._handle.write("\n".join(self._buffered_entry))
          self._handle.write("\n")
      self._buffered_entry = lines
      self._entry_count += 1

  def close(self) -> str:
      if self._handle is None:
          raise RuntimeError("StreamingJsonWriter is not open")
      if self._buffered_entry is not None:
          self._handle.write("\n".join(self._buffered_entry))
          self._handle.write("\n")
          self._buffered_entry = None
      self._handle.write("}\n")
      self._handle.close()
      self._handle = None
      if os.path.exists(self._final_path):
          os.remove(self._final_path)
      os.replace(self._tmp_path, self._final_path)
      return self._final_path


def write_master_from_entries(
    output_dir: str,
    filename: str,
    entries: List[Tuple[str, Any]],
) -> str:
    """Write a complete master file from sorted (key, value) pairs."""
    writer = StreamingJsonWriter(output_dir, filename)
    writer.open()
    for key, value in sorted(entries, key=lambda item: item[0]):
        writer.write_entry(key, value)
    return writer.close()


def master_bytes_from_entries(entries: List[Tuple[str, Any]]) -> bytes:
    """Serialize entries to bytes (for golden parity checks)."""
    sorted_entries = sorted(entries, key=lambda item: item[0])
    parts = ["{"]
    for index, (key, value) in enumerate(sorted_entries):
        entry_lines = _format_root_entry(key, value)
        if index:
            parts[-1] = parts[-1] + ","
        parts.extend(entry_lines)
    parts.append("}")
    parts.append("")
    return "\n".join(parts).encode("utf-8")
