import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_type: Mapped[str | None] = mapped_column(String(64))
    category: Mapped[str | None] = mapped_column(String(64))
    priority: Mapped[str | None] = mapped_column(String(16))
    confidence: Mapped[float | None] = mapped_column(Numeric(5, 2))
    reward_score: Mapped[float | None] = mapped_column(Numeric(8, 4))
    approval_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    rejection_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    application_rate: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback_count: Mapped[int | None] = mapped_column(Integer, default=0)
    last_trained_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expected_impact: Mapped[str | None] = mapped_column(Text)
    action_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="pending")
    assigned_user_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"))
    lot_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("lots.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecommendationFeedback(Base):
    __tablename__ = "recommendation_feedback"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE")
    )
    agent_type: Mapped[str] = mapped_column(String(64), nullable=False)
    action_taken: Mapped[str] = mapped_column(String(32), nullable=False)
    outcome_metric: Mapped[str | None] = mapped_column(String(64))
    outcome_value: Mapped[float | None] = mapped_column(Numeric(14, 4))
    reward_value: Mapped[float | None] = mapped_column(Numeric(8, 4))
    model_version: Mapped[str | None] = mapped_column(String(32))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class RecommendationTrainingRun(Base):
    __tablename__ = "recommendation_training_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    recommendation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("recommendations.id", ondelete="CASCADE"), nullable=False
    )
    training_run: Mapped[str] = mapped_column(String(64), nullable=False)
    reward: Mapped[float | None] = mapped_column(Numeric(8, 4))
    confidence_before: Mapped[float | None] = mapped_column(Numeric(5, 2))
    confidence_after: Mapped[float | None] = mapped_column(Numeric(5, 2))
    feedback_count: Mapped[int | None] = mapped_column(Integer)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
