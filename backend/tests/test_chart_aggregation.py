"""Deep analytics / chart aggregation tests."""

from __future__ import annotations

from collections import Counter

import pytest

from app.services.chart_aggregation import _segments, _trend_points
from app.services.deep_analytics import BLOCKED_DIE_HEATMAP, BLOCKED_SIMILARITY, _blocked_meta


def test_segments_from_counter():
    data = Counter({"functional": 5, "transition": 3})
    segs = _segments(data)
    assert len(segs) == 2
    assert segs[0]["name"] == "functional"
    assert segs[0]["value"] == 5
    assert "color" in segs[0]


def test_trend_points_ordering():
    points = _trend_points({"Mon": 2, "Tue": 5, "Wed": 1})
    assert points[-1]["label"] == "Wed"
    assert points[-1]["value"] == 1


def test_blocked_meta_shape():
    meta = _blocked_meta("patternSimilarityMatrix", BLOCKED_SIMILARITY)
    assert meta["patternSimilarityMatrix"]["status"] == "blocked"
    assert meta["patternSimilarityMatrix"]["blockedBy"] == "pattern_embeddings"


def test_die_heatmap_blocked_spec():
    assert BLOCKED_DIE_HEATMAP["blockedBy"] == "die_results"
