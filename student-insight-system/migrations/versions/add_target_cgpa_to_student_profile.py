"""add target_cgpa to student_profile

Revision ID: add_target_cgpa_001
Revises: b13f43537333
Create Date: 2026-02-22

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_target_cgpa_001'
down_revision = 'b13f43537333'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('student_profile', sa.Column('target_cgpa', sa.Float(), nullable=True))


def downgrade():
    op.drop_column('student_profile', 'target_cgpa')
