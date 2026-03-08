"""add mood_score to weekly_updates

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7a8'
down_revision = 'a2b3c4d5e6f7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weekly_updates', sa.Column('mood_score', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('weekly_updates', 'mood_score')
