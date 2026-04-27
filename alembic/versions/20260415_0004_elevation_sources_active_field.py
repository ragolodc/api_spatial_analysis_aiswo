"""Add is_active to elevation_sources and seed Planetary Computer default source

Revision ID: 20260415_0004
Revises: 20260415_0003
Create Date: 2026-04-15 00:00:00
"""

import sqlalchemy as sa

from alembic import op

revision = "20260415_0004"
down_revision = "20260415_0003"
branch_labels = None
depends_on = None

_PC_SOURCE_ID = "00000000-0000-0000-0000-000000000001"
_PC_CATALOG_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
_PC_COLLECTION = "cop-dem-glo-30"


def upgrade() -> None:
    op.add_column(
        "elevation_sources",
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="false"),
    )
    op.add_column(
        "elevation_sources",
        sa.Column("collection", sa.String(length=200), nullable=True),
    )

    # Seed the default Planetary Computer DEM source as the active one
    op.execute(
        f"""
        INSERT INTO elevation_sources (id, name, srid, source_url, collection, is_active)
        VALUES (
            '{_PC_SOURCE_ID}',
            'Copernicus DEM GLO-30 (Planetary Computer)',
            4326,
            '{_PC_CATALOG_URL}',
            '{_PC_COLLECTION}',
            true
        )
        ON CONFLICT (id) DO NOTHING
        """
    )


def downgrade() -> None:
    op.execute(f"DELETE FROM elevation_sources WHERE id = '{_PC_SOURCE_ID}'")
    op.drop_column("elevation_sources", "collection")
    op.drop_column("elevation_sources", "is_active")
