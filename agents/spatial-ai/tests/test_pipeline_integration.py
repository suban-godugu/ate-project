"""Pipeline / prediction integration tests (require model + sample image)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.config import MODEL_PATH


@pytest.fixture(scope="module")
def ensure_model():
    if not MODEL_PATH.is_file():
        pytest.skip(f"{MODEL_PATH} missing")


def test_pipeline_includes_spatial_analysis(sample_image_path, ensure_model):
    if sample_image_path is None:
        pytest.skip("No sample image in wafer dataset/data/test")

    from src.wafer_pipeline import run_wafer_analysis

    result = run_wafer_analysis(
        sample_image_path,
        save_log=False,
        include_images=False,
    )
    assert "classification" in result
    assert "yield_summary" in result
    assert "dies" in result
    assert "visualization" in result
    assert result["visualization"]["coordinate_space"] == {
        "width": 224,
        "height": 224,
        "units": "model_pixels",
    }
    assert len(result["visualization"]["density"]["points"]) == result["yield_summary"]["fail_dies"]
    assert "spatial_analysis" in result
    spatial = result["spatial_analysis"]
    assert spatial is not None
    assert "cluster_summary" in spatial
    assert "clusters" in spatial
    assert "zone_analysis" in spatial
    assert len(spatial["zone_analysis"]) == 6


def test_predict_api_smoke(sample_image_path, ensure_model):
    if sample_image_path is None:
        pytest.skip("No sample image")

    from fastapi.testclient import TestClient

    from src.api import create_app

    app = create_app()
    with TestClient(app) as client:
        with Path(sample_image_path).open("rb") as handle:
            response = client.post(
                "/predict",
                files={"image": (sample_image_path.name, handle, "image/jpeg")},
                data={"grid_mode": "automatic"},
            )
    assert response.status_code == 200
    body = response.json()
    assert "classification" in body
    assert "spatial_analysis" in body
    assert "visualization" in body
    assert body["visualization"]["density"]["type"] == "gaussian_kde"
    # Legacy PNG panels stay on by default; canvas clients opt out.
    assert "images" in body
    # must not wrap prediction in status/error envelope
    assert "defect_type" in body["classification"]
