"""add_slope_analysis_jobs_table

Revision ID: 20260423_0007
Revises: 20260420_0006
Create Date: 2026-04-23 13:37:31.819343
"""

import sqlalchemy as sa

from alembic import op

revision = "20260423_0007"
down_revision = "20260420_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "slope_analysis_jobs",
        sa.Column("request_id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("result_payload", sa.JSON(), nullable=True),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column(
            "queued_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("request_id"),
    )
    op.create_index(
        "ix_slope_analysis_jobs_zone_id",
        "slope_analysis_jobs",
        ["zone_id"],
    )
    op.create_index(
        "ix_slope_analysis_jobs_status",
        "slope_analysis_jobs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_slope_analysis_jobs_status", table_name="slope_analysis_jobs")
    op.drop_index("ix_slope_analysis_jobs_zone_id", table_name="slope_analysis_jobs")
    op.drop_table("slope_analysis_jobs")
