"""add elevation analysis tables

Revision ID: 20260415_0003
Revises: 20260415_0002
Create Date: 2026-04-15 00:00:00
"""

import sqlalchemy as sa
from alembic import op
from geoalchemy2 import Geometry

revision = "20260415_0003"
down_revision = "20260415_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "elevation_analyses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("resolution_m", sa.Float(), nullable=False),
        sa.Column(
            "analyzed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_elevation_analyses_zone_id", "elevation_analyses", ["zone_id"])

    op.create_table(
        "elevation_points",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("analysis_id", sa.UUID(), nullable=False),
        sa.Column(
            "point_type",
            sa.Enum("highest", "lowest", "centroid", name="elevation_point_type_enum"),
            nullable=False,
        ),
        sa.Column("geometry", Geometry(geometry_type="POINT", srid=4326), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(
            ["analysis_id"], ["elevation_analyses.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_elevation_points_analysis_id", "elevation_points", ["analysis_id"])

    op.create_table(
        "elevation_contours",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("zone_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(length=100), nullable=False),
        sa.Column("interval_m", sa.Float(), nullable=False),
        sa.Column("elevation_m", sa.Float(), nullable=False),
        sa.Column(
            "geometry",
            Geometry(geometry_type="MULTILINESTRING", srid=4326),
            nullable=False,
        ),
        sa.Column(
            "generated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_elevation_contours_zone_id", "elevation_contours", ["zone_id"])


def downgrade() -> None:
    op.drop_index("ix_elevation_contours_zone_id", table_name="elevation_contours")
    op.drop_table("elevation_contours")

    op.drop_index("ix_elevation_points_analysis_id", table_name="elevation_points")
    op.drop_table("elevation_points")
    op.execute("DROP TYPE IF EXISTS elevation_point_type_enum")

    op.drop_index("ix_elevation_analyses_zone_id", table_name="elevation_analyses")
    op.drop_table("elevation_analyses")
