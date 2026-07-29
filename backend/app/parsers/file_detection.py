import enum
import gzip
import re
from pathlib import PurePath

from app.parsers.pat_parser import looks_like_pat_content, pat_text_markers_match
from app.parsers.stil_parser import _STIL_VERSION_RE
from app.parsers.wgl_parser import _WGL_PROGRAM_START


class DetectedFormat(str, enum.Enum):
    stdf = "stdf"
    log = "log"
    stil = "stil"
    wgl = "wgl"
    pat = "pat"
    unrecognized = "unrecognized"


_STDF_EXTENSIONS = {".stdf", ".std"}
_LOG_EXTENSIONS = {".log", ".txt"}
_STIL_EXTENSIONS = {".stil"}
_WGL_EXTENSIONS = {".wgl"}
_PAT_EXTENSIONS = {".pat"}


def _looks_like_stdf(data: bytes) -> bool:
    if len(data) < 6:
        return False
    rec_len = int.from_bytes(data[0:2], "little")
    rec_typ = data[2]
    rec_sub = data[3]
    return rec_typ == 0 and rec_sub == 10 and rec_len >= 2


def _peek_text(data: bytes, limit: int = 8192) -> str:
    return data[:limit].decode("utf-8", errors="replace")


def _looks_like_wgl(data: bytes) -> bool:
    sample = _peek_text(data, 4096)
    if _STIL_VERSION_RE.search(sample):
        return False
    first_lines = [
        ln.strip() for ln in sample.splitlines() if ln.strip() and not ln.strip().startswith("!")
    ]
    if not first_lines:
        return False
    return bool(_WGL_PROGRAM_START.match(first_lines[0]))


def _looks_like_stil(data: bytes) -> bool:
    if _looks_like_wgl(data):
        return False
    sample = _peek_text(data, 4096)
    if _STIL_VERSION_RE.search(sample):
        return True
    if re.search(r"(?m)^\s*(Header|Signals|SignalGroups|Timing|ScanStructures|Pattern)\s*\{", sample):
        return bool(re.search(r"STIL\s+[\d.]+", sample, re.IGNORECASE))
    return False


def _looks_like_pat(data: bytes, logical_name: str) -> bool:
    if _looks_like_stdf(data) or _looks_like_stil(data) or _looks_like_wgl(data):
        return False
    sample = _peek_text(data, 4096)
    if _LOG_MARKERS.search(sample) and not pat_text_markers_match(data):
        return False
    return looks_like_pat_content(data, logical_name)


_LOG_MARKERS = re.compile(
    r"(?i)(lot\s*[:=]|wafer\s*[:=]|tester\s*[:=]|pattern|scan\s*chain|yield|defect|mbist|lbist|"
    r"fail(?:ure)?|pass(?:ed)?|product|fab|program|test\s+log|ate\s+log|stdf|datalog)",
)


def _looks_like_log(text: str) -> bool:
    if not text.strip():
        return False
    printable_ratio = sum(1 for ch in text[:4096] if ch.isprintable() or ch in "\r\n\t") / max(
        len(text[:4096]), 1
    )
    if printable_ratio < 0.85:
        return False
    return bool(_LOG_MARKERS.search(text[:8192]))


def _normalize_for_detection(file_name: str, data: bytes) -> tuple[str, bytes]:
    """Handle compressed pattern files for content inspection."""
    ext = PurePath(file_name).suffix.lower()
    if ext == ".gz":
        stem = PurePath(file_name).stem
        if stem.lower().endswith((".stil", ".wgl", ".pat")):
            try:
                return stem, gzip.decompress(data)
            except gzip.BadGzipFile:
                return file_name, data
    return file_name, data


def detect_file_format(file_name: str, data: bytes) -> DetectedFormat:
    logical_name, payload = _normalize_for_detection(file_name, data)
    ext = PurePath(logical_name).suffix.lower()

    if ext in _STDF_EXTENSIONS or _looks_like_stdf(payload):
        return DetectedFormat.stdf

    if ext in _WGL_EXTENSIONS or logical_name.lower().endswith(".wgl") or _looks_like_wgl(payload):
        return DetectedFormat.wgl

    if ext in _STIL_EXTENSIONS or logical_name.lower().endswith(".stil") or _looks_like_stil(payload):
        return DetectedFormat.stil

    if _looks_like_pat(payload, logical_name):
        return DetectedFormat.pat

    if ext in _LOG_EXTENSIONS:
        try:
            text = payload.decode("utf-8", errors="replace")
        except Exception:
            return DetectedFormat.unrecognized
        if _looks_like_log(text):
            return DetectedFormat.log
        return DetectedFormat.unrecognized

    if _looks_like_stdf(payload):
        return DetectedFormat.stdf
    if _looks_like_wgl(payload):
        return DetectedFormat.wgl
    if _looks_like_stil(payload):
        return DetectedFormat.stil
    if _looks_like_pat(payload, logical_name):
        return DetectedFormat.pat

    return DetectedFormat.unrecognized
