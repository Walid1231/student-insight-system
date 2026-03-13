"""add student_code to student_profile

Revision ID: f1a2b3c4d5e6
Revises: e38e38a9c801
Create Date: 2026-03-13 23:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e38e38a9c801'
branch_labels = None
depends_on = None


def upgrade():
    # Add the student_code column (nullable initially for data migration)
    with op.batch_alter_table('student_profile', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('student_code', sa.String(16), nullable=True)
        )
        batch_op.create_index('ix_student_profile_student_code', ['student_code'], unique=True)

    # Data migration: assign sequential codes to existing rows that lack one
    conn = op.get_bind()
    rows = conn.execute(
        sa.text("SELECT id FROM student_profile WHERE student_code IS NULL ORDER BY id")
    ).fetchall()
    for seq, row in enumerate(rows, start=1):
        code = str(seq).zfill(16)
        conn.execute(
            sa.text("UPDATE student_profile SET student_code = :code WHERE id = :id"),
            {"code": code, "id": row[0]},
        )


def downgrade():
    with op.batch_alter_table('student_profile', schema=None) as batch_op:
        batch_op.drop_index('ix_student_profile_student_code')
        batch_op.drop_column('student_code')
