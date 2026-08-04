"""Streaming file readers for large ATE/STDF inputs."""

from __future__ import annotations

import mmap
from pathlib import Path
from typing import Iterator


def iter_lines(path: Path, *, start_line: int = 0, encoding: str = "utf-8") -> Iterator[tuple[int, str]]:
    """Yield (1-based line_no, line) starting at start_line (0 = from beginning)."""
    with path.open("r", encoding=encoding, errors="ignore") as fh:
        for lineno, line in enumerate(fh, start=1):
            if lineno <= start_line:
                continue
            yield lineno, line


def iter_chunks(path: Path, *, chunk_size: int = 8 * 1024 * 1024, start_offset: int = 0) -> Iterator[tuple[int, bytes]]:
    """Yield (offset, bytes_chunk) for binary/chunk parsing."""
    with path.open("rb") as fh:
        if start_offset:
            fh.seek(start_offset)
        offset = start_offset
        while True:
            data = fh.read(chunk_size)
            if not data:
                break
            yield offset, data
            offset += len(data)


def mmap_bytes(path: Path) -> memoryview:
    """Memory-map a file for zero-copy reads (caller must keep file open via context)."""
    with path.open("rb") as fh:
        with mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            return memoryview(bytes(mm))  # snapshot safe for short-lived use


def file_size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
