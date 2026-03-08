"""add goals_achieved to weekly_updates

Revision ID: f1a2b3c4d5e6
Revises: e38e38a9c801
Create Date: 2026-03-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e38e38a9c801'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('weekly_updates', sa.Column('goals_achieved', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('weekly_updates', 'goals_achieved')
