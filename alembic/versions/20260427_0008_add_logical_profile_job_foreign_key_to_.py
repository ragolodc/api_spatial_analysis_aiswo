"""add_logical_profile_job_foreign_key_to_slope_job_table

Revision ID: 20260427_0008
Revises: 20260423_0007
Create Date: 2026-04-27 12:24:34.690203
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260427_0008"
down_revision = "20260423_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "slope_analysis_jobs",
        sa.Column("profile_analysis_id", sa.UUID(), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("slope_analysis_jobs", "profile_analysis_id")
