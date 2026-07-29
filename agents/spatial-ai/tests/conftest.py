"""
Shared pytest fixtures for WaferVision-AI.
"""

from __future__ import annotations

from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture
def sample_dies() -> list[dict]:
    """Synthetic die grid for cluster / zone unit tests (no model required)."""
    dies: list[dict] = []
    die_id = 1
    # 6x6 grid around image center (112, 112) pitch 10
    for row in range(6):
        for col in range(6):
            x = 90 + col * 10
            y = 90 + row * 10
            # A connected FAIL blob in the top-left of the grid
            status = "FAIL" if row < 2 and col < 3 else "GOOD"
            dies.append(
                {
                    "die_id": die_id,
                    "row": row,
                    "column": col,
                    "x": x,
                    "y": y,
                    "bbox": {"x0": x - 4, "y0": y - 4, "x1": x + 4, "y1": y + 4},
                    "status": status,
                }
            )
            die_id += 1
    return dies


@pytest.fixture
def sample_geometry() -> dict:
    return {"center_x": 112.0, "center_y": 112.0, "radius": 100.0}


@pytest.fixture
def sample_yield(sample_dies: list[dict]) -> dict:
    good = sum(1 for d in sample_dies if d["status"] == "GOOD")
    fail = sum(1 for d in sample_dies if d["status"] == "FAIL")
    total = len(sample_dies)
    return {
        "good_dies": good,
        "fail_dies": fail,
        "total_dies": total,
        "yield_percent": round(100.0 * good / total, 4),
    }


@pytest.fixture
def sample_image_path() -> Path | None:
    roots = list((PROJECT_ROOT / "wafer dataset" / "data" / "test").rglob("*.jpg"))
    return roots[0] if roots else None
