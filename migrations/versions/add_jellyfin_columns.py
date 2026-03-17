"""Add jellyfin_user_id and jellyfin_password columns to users table

Revision ID: a1b2c3d4e5f6
Revises: dd47928355f1
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "dd47928355f1"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("jellyfin_user_id", sa.String(64), nullable=True))
    op.add_column("users", sa.Column("jellyfin_password", sa.String(256), nullable=True))


def downgrade():
    op.drop_column("users", "jellyfin_password")
    op.drop_column("users", "jellyfin_user_id")
