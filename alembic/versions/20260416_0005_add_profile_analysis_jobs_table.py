"""add profile analysis jobs table

Revision ID: 20260416_0005
Revises: 20260415_0004
Create Date: 2026-04-16 00:00:00
"""

import sqlalchemy as sa
from alembic import op

revision = "20260416_0005"
down_revision = "20260415_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "profile_analysis_jobs",
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
        "ix_profile_analysis_jobs_zone_id",
        "profile_analysis_jobs",
        ["zone_id"],
    )
    op.create_index(
        "ix_profile_analysis_jobs_status",
        "profile_analysis_jobs",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_profile_analysis_jobs_status", table_name="profile_analysis_jobs")
    op.drop_index("ix_profile_analysis_jobs_zone_id", table_name="profile_analysis_jobs")
    op.drop_table("profile_analysis_jobs")
