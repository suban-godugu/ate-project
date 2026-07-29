"""Redundancy detection schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


class RedundantPattern(BaseModel):
    """Redundancy classification for one pattern within a cluster."""

    pattern_id: str
    cluster_id: str
    representative_pattern: str
    similarity_to_representative: float = 0.0
    cluster_average_similarity: float = 0.0
    is_representative: bool = False
    redundant_flag: bool = False


class ClusterSummary(BaseModel):
    """Canonical summary of one similarity cluster."""

    cluster_id: str
    representative: str
    members: list[str] = Field(default_factory=list)
    redundant_members: list[str] = Field(default_factory=list)
    cluster_size: int = 0
    average_similarity: float = 0.0


class RedundancyList(BaseModel):
    """All confirmed redundant patterns."""

    patterns: list[RedundantPattern] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None
    similarity_threshold: float = 0.0


class ClusterList(BaseModel):
    """All cluster summaries."""

    clusters: list[ClusterSummary] = Field(default_factory=list)
    total: int = 0
    built_at: datetime | None = None
    similarity_threshold: float = 0.0


class RedundancyStatistics(BaseModel):
    """Aggregate redundancy statistics."""

    clusters: int = 0
    representatives: int = 0
    redundant_patterns: int = 0
    average_cluster_size: float = 0.0
    average_similarity: float = 0.0


class RedundancyRefreshResponse(BaseModel):
    """Refresh acknowledgement for redundancy analysis."""

    success: bool = True
    message: str
    data: RedundancyStatistics
