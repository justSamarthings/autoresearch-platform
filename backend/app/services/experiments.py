from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.models import Checkpoint, Experiment, ExperimentMetric
from backend.app.schemas.experiment import ExperimentIngestRequest

SUMMARY_METRIC_KEYS = (
    "val_bpb",
    "training_seconds",
    "total_seconds",
    "peak_vram_mb",
    "mfu_percent",
    "total_tokens",
    "num_steps",
    "num_params",
)


def _cfg_get(configuration: dict[str, Any] | None, key: str) -> Any:
    if not configuration:
        return None
    return configuration.get(key)


def get_experiment_by_key(db: Session, experiment_id: str) -> Experiment | None:
    stmt = (
        select(Experiment)
        .where(Experiment.experiment_id == experiment_id)
        .options(selectinload(Experiment.metrics), selectinload(Experiment.checkpoints))
    )
    return db.scalars(stmt).first()


def list_experiments(
    db: Session,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
) -> tuple[list[Experiment], int]:
    filters = []
    if status:
        filters.append(Experiment.status == status)

    count_stmt = select(func.count()).select_from(Experiment)
    list_stmt: Select[tuple[Experiment]] = select(Experiment)
    if filters:
        count_stmt = count_stmt.where(*filters)
        list_stmt = list_stmt.where(*filters)

    total = db.scalar(count_stmt) or 0
    items = db.scalars(
        list_stmt.order_by(Experiment.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total


def ingest_experiment(db: Session, payload: ExperimentIngestRequest) -> tuple[Experiment, bool]:
    existing = get_experiment_by_key(db, payload.experiment_id)
    if existing is not None:
        return existing, False

    configuration = payload.configuration or {}
    completed_at = datetime.now(timezone.utc)
    started_at = None
    if payload.total_seconds is not None:
        started_at = completed_at - timedelta(seconds=float(payload.total_seconds))

    experiment = Experiment(
        experiment_id=payload.experiment_id,
        status=payload.status,
        git_commit=payload.git_commit,
        git_dirty=payload.git_dirty,
        parent_experiment_id=payload.parent_experiment_id,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=payload.training_seconds,
        val_bpb=payload.val_bpb,
        num_params=payload.num_params,
        depth=payload.depth,
        vocab_size=_cfg_get(configuration, "vocab_size"),
        max_seq_len=_cfg_get(configuration, "max_seq_len"),
        window_pattern=_cfg_get(configuration, "window_pattern"),
        checkpoint_path=payload.checkpoint_path,
        configuration=configuration,
        crash_message=payload.crash_message,
    )
    db.add(experiment)
    db.flush()

    step = payload.num_steps
    raw = payload.model_dump()
    for name in SUMMARY_METRIC_KEYS:
        value = raw.get(name)
        if value is None:
            continue
        db.add(
            ExperimentMetric(
                experiment_uuid=experiment.id,
                metric_name=name,
                metric_value=float(value),
                step=step,
            )
        )

    if payload.checkpoint_path:
        db.add(
            Checkpoint(
                experiment_uuid=experiment.id,
                checkpoint_path=payload.checkpoint_path,
                metadata_json={
                    "experiment_id": payload.experiment_id,
                    "git_commit": payload.git_commit,
                    "git_dirty": payload.git_dirty,
                    "val_bpb": payload.val_bpb,
                    "depth": payload.depth,
                    "num_params": payload.num_params,
                    "vocab_size": _cfg_get(configuration, "vocab_size"),
                    "max_seq_len": _cfg_get(configuration, "max_seq_len"),
                    "window_pattern": _cfg_get(configuration, "window_pattern"),
                },
            )
        )

    db.commit()
    refreshed = get_experiment_by_key(db, payload.experiment_id)
    assert refreshed is not None
    return refreshed, True


def get_checkpoint(db: Session, checkpoint_id: UUID) -> Checkpoint | None:
    return db.get(Checkpoint, checkpoint_id)


def list_checkpoints(
    db: Session, *, limit: int = 50, offset: int = 0
) -> tuple[list[Checkpoint], int]:
    total = db.scalar(select(func.count()).select_from(Checkpoint)) or 0
    items = db.scalars(
        select(Checkpoint).order_by(Checkpoint.created_at.desc()).limit(limit).offset(offset)
    ).all()
    return list(items), total
