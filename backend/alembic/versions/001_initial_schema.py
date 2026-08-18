"""initial experiment schema

Revision ID: 001_initial
Revises:
Create Date: 2026-08-18
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "experiments",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("git_commit", sa.String(length=64), nullable=True),
        sa.Column("git_dirty", sa.Boolean(), nullable=True),
        sa.Column("parent_experiment_id", sa.String(length=128), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_seconds", sa.Float(), nullable=True),
        sa.Column("val_bpb", sa.Float(), nullable=True),
        sa.Column("num_params", sa.Integer(), nullable=True),
        sa.Column("depth", sa.Integer(), nullable=True),
        sa.Column("vocab_size", sa.Integer(), nullable=True),
        sa.Column("max_seq_len", sa.Integer(), nullable=True),
        sa.Column("window_pattern", sa.String(length=32), nullable=True),
        sa.Column("checkpoint_path", sa.Text(), nullable=True),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column("crash_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["parent_experiment_id"],
            ["experiments.experiment_id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("experiment_id"),
    )
    op.create_index("ix_experiments_experiment_id", "experiments", ["experiment_id"])
    op.create_index("ix_experiments_status", "experiments", ["status"])
    op.create_index("ix_experiments_val_bpb", "experiments", ["val_bpb"])

    op.create_table(
        "experiment_metrics",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_uuid", sa.Uuid(), nullable=False),
        sa.Column("metric_name", sa.String(length=64), nullable=False),
        sa.Column("metric_value", sa.Float(), nullable=False),
        sa.Column("step", sa.Integer(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["experiment_uuid"], ["experiments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "experiment_uuid",
            "metric_name",
            "step",
            name="uq_experiment_metric_name_step",
        ),
    )
    op.create_index("ix_experiment_metrics_experiment_uuid", "experiment_metrics", ["experiment_uuid"])
    op.create_index("ix_experiment_metrics_metric_name", "experiment_metrics", ["metric_name"])

    op.create_table(
        "checkpoints",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("experiment_uuid", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_path", sa.Text(), nullable=False),
        sa.Column(
            "metadata",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["experiment_uuid"], ["experiments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_checkpoints_experiment_uuid", "checkpoints", ["experiment_uuid"])

    op.create_table(
        "evaluations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("experiment_uuid", sa.Uuid(), nullable=True),
        sa.Column("dataset", sa.String(length=128), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "configuration",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column(
            "metrics",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checkpoint_id"], ["checkpoints.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["experiment_uuid"], ["experiments.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_evaluations_checkpoint_id", "evaluations", ["checkpoint_id"])
    op.create_index("ix_evaluations_experiment_uuid", "evaluations", ["experiment_uuid"])

    op.create_table(
        "inference_runs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("checkpoint_id", sa.Uuid(), nullable=False),
        sa.Column("prompt", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column(
            "generation_params",
            postgresql.JSONB(astext_type=sa.Text()).with_variant(sa.JSON(), "sqlite"),
            nullable=True,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["checkpoint_id"], ["checkpoints.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_inference_runs_checkpoint_id", "inference_runs", ["checkpoint_id"])


def downgrade() -> None:
    op.drop_index("ix_inference_runs_checkpoint_id", table_name="inference_runs")
    op.drop_table("inference_runs")
    op.drop_index("ix_evaluations_experiment_uuid", table_name="evaluations")
    op.drop_index("ix_evaluations_checkpoint_id", table_name="evaluations")
    op.drop_table("evaluations")
    op.drop_index("ix_checkpoints_experiment_uuid", table_name="checkpoints")
    op.drop_table("checkpoints")
    op.drop_index("ix_experiment_metrics_metric_name", table_name="experiment_metrics")
    op.drop_index("ix_experiment_metrics_experiment_uuid", table_name="experiment_metrics")
    op.drop_table("experiment_metrics")
    op.drop_index("ix_experiments_val_bpb", table_name="experiments")
    op.drop_index("ix_experiments_status", table_name="experiments")
    op.drop_index("ix_experiments_experiment_id", table_name="experiments")
    op.drop_table("experiments")
