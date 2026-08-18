import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON, Uuid

from backend.app.db.base import Base

JSONType = JSON().with_variant(JSONB(), "postgresql")
UUIDType = Uuid(as_uuid=True).with_variant(UUID(as_uuid=True), "postgresql")


class Experiment(Base):
    __tablename__ = "experiments"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    experiment_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    git_commit: Mapped[str | None] = mapped_column(String(64), nullable=True)
    git_dirty: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    parent_experiment_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("experiments.experiment_id", ondelete="SET NULL"),
        nullable=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    val_bpb: Mapped[float | None] = mapped_column(Float, nullable=True, index=True)
    num_params: Mapped[int | None] = mapped_column(Integer, nullable=True)
    depth: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vocab_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_seq_len: Mapped[int | None] = mapped_column(Integer, nullable=True)
    window_pattern: Mapped[str | None] = mapped_column(String(32), nullable=True)
    checkpoint_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    configuration: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    crash_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    metrics: Mapped[list["ExperimentMetric"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )
    checkpoints: Mapped[list["Checkpoint"]] = relationship(
        back_populates="experiment", cascade="all, delete-orphan"
    )


class ExperimentMetric(Base):
    __tablename__ = "experiment_metrics"
    __table_args__ = (
        UniqueConstraint(
            "experiment_uuid",
            "metric_name",
            "step",
            name="uq_experiment_metric_name_step",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    experiment_uuid: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    metric_name: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    metric_value: Mapped[float] = mapped_column(Float, nullable=False)
    step: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped[Experiment] = relationship(back_populates="metrics")


class Checkpoint(Base):
    __tablename__ = "checkpoints"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    experiment_uuid: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("experiments.id", ondelete="CASCADE"), nullable=False, index=True
    )
    checkpoint_path: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    experiment: Mapped[Experiment] = relationship(back_populates="checkpoints")
    evaluations: Mapped[list["Evaluation"]] = relationship(back_populates="checkpoint")
    inference_runs: Mapped[list["InferenceRun"]] = relationship(back_populates="checkpoint")


class Evaluation(Base):
    """Schema reserved for Phase 7 — no workflow in Phase 3."""

    __tablename__ = "evaluations"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    experiment_uuid: Mapped[uuid.UUID | None] = mapped_column(
        UUIDType, ForeignKey("experiments.id", ondelete="SET NULL"), nullable=True, index=True
    )
    dataset: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    configuration: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    metrics: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    checkpoint: Mapped[Checkpoint] = relationship(back_populates="evaluations")


class InferenceRun(Base):
    """Schema reserved for Phase 7 — no workflow in Phase 3."""

    __tablename__ = "inference_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUIDType, primary_key=True, default=uuid.uuid4)
    checkpoint_id: Mapped[uuid.UUID] = mapped_column(
        UUIDType, ForeignKey("checkpoints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    output_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_params: Mapped[dict | None] = mapped_column(JSONType, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    checkpoint: Mapped[Checkpoint] = relationship(back_populates="inference_runs")
