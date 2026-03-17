"""add is_read to student_note

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-03-17

"""
from alembic import op
import sqlalchemy as sa

revision = 'd5e6f7a8b9c0'
down_revision = 'c4d5e6f7a8b9'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('student_note', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_read', sa.Boolean(), nullable=False, server_default='false'))


def downgrade():
    with op.batch_alter_table('student_note', schema=None) as batch_op:
        batch_op.drop_column('is_read')
