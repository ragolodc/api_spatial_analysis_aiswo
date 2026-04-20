"""replace_provider_with_source_id_in_analyses_and_contours

Revision ID: 20260420_0006
Revises: 20260416_0005
Create Date: 2026-04-20 09:10:26.432236
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision = "20260420_0006"
down_revision = "20260416_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # limpiar datos exisytentes que ya no son compatibles
    op.execute("TRUNCATE TABLE elevation_analyses CASCADE")
    op.execute("TRUNCATE TABLE elevation_contours CASCADE")
    # elevation_sources: agregar resolution_m
    op.add_column(
        "elevation_sources",
        sa.Column("resolution_m", sa.Float(), nullable=False, server_default="30.0"),
    )
    op.alter_column("elevation_sources", "resolution_m", server_default=None)

    # elevation_analyses: quitar provider y resolution_m, agregar source_id FK
    op.drop_column("elevation_analyses", "provider")
    op.drop_column("elevation_analyses", "resolution_m")
    op.add_column(
        "elevation_analyses", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False)
    )
    op.create_foreign_key(
        "fk_elevation_analyses_source_id",
        "elevation_analyses",
        "elevation_sources",
        ["source_id"],
        ["id"],
    )

    # elevation_contours: quitar provider, agregar source_id FK
    op.drop_column("elevation_contours", "provider")
    op.add_column(
        "elevation_contours", sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False)
    )
    op.create_foreign_key(
        "fk_elevation_contours_source_id",
        "elevation_contours",
        "elevation_sources",
        ["source_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_elevation_contours_source_id", "elevation_contours", type_="foreignkey")
    op.drop_column("elevation_contours", "source_id")
    op.add_column(
        "elevation_contours",
        sa.Column("provider", sa.String(), nullable=False, server_default="unknown"),
    )
    op.alter_column("elevation_contours", "provider", server_default=None)
    op.drop_constraint("fk_elevation_analyses_source_id", "elevation_analyses", type_="foreignkey")
    op.drop_column("elevation_analyses", "source_id")
    op.add_column(
        "elevation_analyses",
        sa.Column("provider", sa.String(), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "elevation_analyses",
        sa.Column("resolution_m", sa.Float(), nullable=False, server_default="30.0"),
    )
    op.alter_column("elevation_analyses", "resolution_m", server_default=None)

    op.drop_column("elevation_sources", "resolution_m")
