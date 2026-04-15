"""add zones table

Revision ID: 20260415_0002
Revises: 20260415_0001
Create Date: 2026-04-15 00:00:00
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision = "20260415_0002"
down_revision = "20260415_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "zones",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column(
            "zone_type",
            sa.Enum("farm_boundary", "pivot", name="zone_type_enum"),
            nullable=False,
        ),
        sa.Column("geometry", Geometry(geometry_type="POLYGON", srid=4326), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("zones")
    op.execute("DROP TYPE IF EXISTS zone_type_enum")
