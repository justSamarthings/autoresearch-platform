from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExperimentIngestRequest(BaseModel):
    """Matches Phase 2 training/artifacts/results/<id>.json."""

    experiment_id: str
    git_commit: str | None = None
    git_dirty: bool | None = None
    status: str
    crash_message: str | None = None
    val_bpb: float | None = None
    training_seconds: float | None = None
    total_seconds: float | None = None
    peak_vram_mb: float | None = None
    mfu_percent: float | None = None
    total_tokens: int | None = None
    num_steps: int | None = None
    num_params: int | None = None
    depth: int | None = None
    checkpoint_path: str | None = None
    configuration: dict[str, Any] | None = None
    parent_experiment_id: str | None = None


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    metric_name: str
    metric_value: float
    step: int | None
    recorded_at: datetime


class CheckpointOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: UUID
    checkpoint_path: str
    metadata: dict[str, Any] | None = Field(
        default=None,
        validation_alias="metadata_json",
        serialization_alias="metadata",
    )
    created_at: datetime


class ExperimentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    experiment_id: str
    status: str
    git_commit: str | None
    git_dirty: bool | None
    parent_experiment_id: str | None
    val_bpb: float | None
    duration_seconds: float | None
    num_params: int | None
    depth: int | None
    vocab_size: int | None
    max_seq_len: int | None
    window_pattern: str | None
    checkpoint_path: str | None
    created_at: datetime


class ExperimentDetail(ExperimentSummary):
    started_at: datetime | None
    completed_at: datetime | None
    configuration: dict[str, Any] | None
    crash_message: str | None
    metrics: list[MetricOut] = []
    checkpoints: list[CheckpointOut] = []


class ExperimentIngestResponse(BaseModel):
    created: bool
    experiment: ExperimentDetail


class ExperimentListResponse(BaseModel):
    items: list[ExperimentSummary]
    total: int
    limit: int
    offset: int
