"""courses

Revision ID: 0002_courses
Revises: a2e7676710c5
Create Date: 2026-10-24 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_courses'
down_revision: Union[str, Sequence[str], None] = 'a2e7676710c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'courses',
        sa.Column('id', sa.UUID(), nullable=False, comment='Identitas unik mata kuliah'),
        sa.Column('code', sa.String(length=50), nullable=False, comment='Kode mata kuliah (unik)'),
        sa.Column('name', sa.String(length=255), nullable=False, comment='Nama mata kuliah'),
        sa.Column('credits', sa.Integer(), nullable=False, comment='Jumlah SKS'),
        sa.Column('semester', sa.String(length=20), nullable=False, comment='Semester (mis. 2026/1)'),
        sa.Column('created_by', sa.UUID(), nullable=False, comment='Pengguna yang membuat data mata kuliah'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Waktu pembuatan data mata kuliah'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code'),
        comment='Tabel mata kuliah'
    )
    op.create_index(op.f('ix_courses_created_by'), 'courses', ['created_by'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_courses_created_by'), table_name='courses')
    op.drop_table('courses')
