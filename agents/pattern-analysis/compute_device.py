"""
Optional CUDA compute backend for Pattern Analysis Agent.

L1 clustering (PA-FR-006) stays on CPU by default so artifact hashes remain
byte-identical. GPU accelerates batch cosine workloads (FR-008 top-N and
optional condensed distance matrices) when CUDA PyTorch is available.
"""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG: Dict[str, Any] = {
    "device": "auto",  # auto | cpu | cuda
    "gpu_similarity": True,
    "gpu_clustering": False,
    "min_patterns_for_gpu": 32,
}

_TORCH = None
_TORCH_IMPORT_ERROR: Optional[str] = None


@dataclass(frozen=True)
class ComputeConfig:
    device_preference: str
    gpu_similarity: bool
    gpu_clustering: bool
    min_patterns_for_gpu: int


@dataclass(frozen=True)
class DeviceInfo:
    requested: str
    resolved: str
    cuda_available: bool
    torch_available: bool
    gpu_name: Optional[str]
    gpu_similarity_enabled: bool
    gpu_clustering_enabled: bool
    detail: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "requested": self.requested,
            "resolved": self.resolved,
            "cuda_available": self.cuda_available,
            "torch_available": self.torch_available,
            "gpu_name": self.gpu_name,
            "gpu_similarity_enabled": self.gpu_similarity_enabled,
            "gpu_clustering_enabled": self.gpu_clustering_enabled,
            "detail": self.detail,
        }


def _try_import_torch():
    global _TORCH, _TORCH_IMPORT_ERROR
    if _TORCH is not None or _TORCH_IMPORT_ERROR is not None:
        return _TORCH
    try:
        import torch  # type: ignore

        _TORCH = torch
        return torch
    except Exception as exc:  # pragma: no cover - environment dependent
        _TORCH_IMPORT_ERROR = str(exc)
        logger.warning("PyTorch unavailable; GPU acceleration disabled (%s)", exc)
        return None


def load_compute_config(config_path: Optional[str] = None) -> ComputeConfig:
    path = config_path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "config", "compute.yaml"
    )
    merged = dict(DEFAULT_CONFIG)
    if os.path.isfile(path):
        with open(path, "r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        section = payload.get("compute") if isinstance(payload, dict) else None
        if isinstance(section, dict):
            merged.update(section)
    preference = str(merged.get("device", "auto")).strip().lower()
    if preference not in {"auto", "cpu", "cuda"}:
        preference = "auto"
    return ComputeConfig(
        device_preference=preference,
        gpu_similarity=bool(merged.get("gpu_similarity", True)),
        gpu_clustering=bool(merged.get("gpu_clustering", False)),
        min_patterns_for_gpu=max(1, int(merged.get("min_patterns_for_gpu", 32))),
    )


@lru_cache(maxsize=1)
def get_device_info(config_path: Optional[str] = None) -> DeviceInfo:
    config = load_compute_config(config_path)
    torch = _try_import_torch()
    torch_available = torch is not None
    cuda_available = bool(torch_available and torch.cuda.is_available())
    gpu_name: Optional[str] = None
    if cuda_available:
        try:
            gpu_name = torch.cuda.get_device_name(0)
        except Exception:  # pragma: no cover
            gpu_name = "CUDA device 0"

    requested = config.device_preference
    if requested == "cpu":
        resolved = "cpu"
        detail = "Forced CPU via config/compute.yaml"
    elif requested == "cuda":
        if cuda_available:
            resolved = "cuda"
            detail = f"Forced CUDA ({gpu_name})"
        else:
            resolved = "cpu"
            detail = (
                f"CUDA requested but unavailable "
                f"(torch_available={torch_available}, err={_TORCH_IMPORT_ERROR})"
            )
    else:
        if cuda_available:
            resolved = "cuda"
            detail = f"Auto-selected CUDA ({gpu_name})"
        else:
            resolved = "cpu"
            detail = (
                "Auto-selected CPU "
                f"(torch_available={torch_available}, cuda_available={cuda_available})"
            )

    return DeviceInfo(
        requested=requested,
        resolved=resolved,
        cuda_available=cuda_available,
        torch_available=torch_available,
        gpu_name=gpu_name,
        gpu_similarity_enabled=bool(config.gpu_similarity and resolved == "cuda"),
        gpu_clustering_enabled=bool(config.gpu_clustering and resolved == "cuda"),
        detail=detail,
    )


def reset_device_cache() -> None:
    get_device_info.cache_clear()


def _torch_device():
    info = get_device_info()
    torch = _try_import_torch()
    if torch is None or info.resolved != "cuda":
        return None, None
    return torch, torch.device("cuda")


def batch_cosine_similarities(
    reference: Sequence[float],
    candidates: Sequence[Sequence[float]],
) -> List[float]:
    """
    Cosine similarity of one reference vector against many candidates.

    Uses CUDA when enabled; falls back to NumPy. Results are float64 host values
    before caller rounding.
    """
    if candidates is None:
        return []
    try:
        n_candidates = len(candidates)
    except TypeError:
        return []
    if n_candidates == 0:
        return []

    info = get_device_info()
    config = load_compute_config()
    use_gpu = (
        info.gpu_similarity_enabled
        and n_candidates >= config.min_patterns_for_gpu
    )

    ref = np.asarray(reference, dtype=np.float64)
    mat = np.asarray(candidates, dtype=np.float64)
    if mat.ndim != 2:
        raise ValueError("candidates must be a 2-D matrix")

    torch, device = _torch_device()
    if use_gpu and torch is not None and device is not None:
        try:
            ref_t = torch.as_tensor(ref, dtype=torch.float64, device=device)
            mat_t = torch.as_tensor(mat, dtype=torch.float64, device=device)
            ref_norm = torch.linalg.vector_norm(ref_t)
            row_norms = torch.linalg.vector_norm(mat_t, dim=1)
            dots = mat_t @ ref_t
            denom = row_norms * ref_norm
            scores = torch.where(
                denom > 0,
                dots / denom,
                torch.zeros_like(dots),
            )
            return [float(x) for x in scores.detach().cpu().tolist()]
        except Exception as exc:  # pragma: no cover - runtime GPU faults
            logger.warning("GPU batch cosine failed; falling back to CPU (%s)", exc)

    ref_norm = float(np.linalg.norm(ref))
    if ref_norm == 0.0:
        return [0.0] * len(mat)
    row_norms = np.linalg.norm(mat, axis=1)
    dots = mat @ ref
    scores = np.zeros(len(mat), dtype=np.float64)
    valid = row_norms > 0.0
    scores[valid] = dots[valid] / (row_norms[valid] * ref_norm)
    return [float(x) for x in scores.tolist()]


def cosine_distance_condensed(matrix: np.ndarray) -> Optional[np.ndarray]:
    """
    Optional GPU condensed cosine distance matrix (upper triangle, scipy order).

    Returns None when GPU clustering is disabled so callers keep SciPy pdist.
    """
    info = get_device_info()
    config = load_compute_config()
    if not info.gpu_clustering_enabled:
        return None
    if matrix.ndim != 2 or matrix.shape[0] < 2:
        return None
    if matrix.shape[0] < config.min_patterns_for_gpu:
        return None

    torch, device = _torch_device()
    if torch is None or device is None:
        return None

    try:
        mat = torch.as_tensor(matrix, dtype=torch.float64, device=device)
        norms = torch.linalg.vector_norm(mat, dim=1, keepdim=True)
        norms = torch.clamp(norms, min=1e-15)
        normalized = mat / norms
        sim = normalized @ normalized.T
        dist = 1.0 - sim
        # SciPy pdist order: row i < j
        idx = torch.triu_indices(dist.shape[0], dist.shape[0], offset=1, device=device)
        condensed = dist[idx[0], idx[1]]
        return condensed.detach().cpu().numpy()
    except Exception as exc:  # pragma: no cover
        logger.warning("GPU condensed cosine failed; falling back to SciPy (%s)", exc)
        return None


def gpu_block_matmul(
    normalized: np.ndarray,
    block_start: int,
    block_end: int,
) -> np.ndarray:
    """
    Block of exact cosine similarities: normalized[block_start:block_end] @ normalized.T.

    CPU is authoritative for CI; uses CUDA when gpu_similarity is enabled and available.
    """
    info = get_device_info()
    config = load_compute_config()
    n = normalized.shape[0]
    use_gpu = info.gpu_similarity_enabled and n >= config.min_patterns_for_gpu

    torch, device = _torch_device()
    if use_gpu and torch is not None and device is not None:
        try:
            mat_t = torch.as_tensor(normalized, dtype=torch.float64, device=device)
            block = mat_t[block_start:block_end] @ mat_t.T
            return block.detach().cpu().numpy()
        except Exception as exc:  # pragma: no cover
            logger.warning("GPU block matmul failed; falling back to CPU (%s)", exc)

    return normalized[block_start:block_end] @ normalized.T


def log_compute_device_at_startup() -> DeviceInfo:
    info = get_device_info()
    logger.info(
        "Compute device: resolved=%s requested=%s cuda=%s gpu=%s similarity_gpu=%s clustering_gpu=%s (%s)",
        info.resolved,
        info.requested,
        info.cuda_available,
        info.gpu_name,
        info.gpu_similarity_enabled,
        info.gpu_clustering_enabled,
        info.detail,
    )
    print(
        f"[compute] device={info.resolved} "
        f"cuda_available={info.cuda_available} "
        f"gpu={info.gpu_name or 'n/a'} "
        f"similarity_gpu={info.gpu_similarity_enabled} "
        f"clustering_gpu={info.gpu_clustering_enabled}"
    )
    return info
