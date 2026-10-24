"""classes, students, enrollments

Revision ID: 0003_classes_students
Revises: 0002_courses
Create Date: 2026-10-24 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0003_classes_students'
down_revision: Union[str, Sequence[str], None] = '0002_courses'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'students',
        sa.Column('id', sa.UUID(), nullable=False, comment='Identitas unik mahasiswa'),
        sa.Column('nim', sa.String(length=50), nullable=False, comment='Nomor Induk Mahasiswa (unik)'),
        sa.Column('full_name', sa.String(length=255), nullable=False, comment='Nama lengkap mahasiswa'),
        sa.Column('email', sa.String(length=255), nullable=True, comment='Email mahasiswa (untuk notifikasi rilis nilai)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Waktu pembuatan data mahasiswa'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nim'),
        comment='Tabel data mahasiswa (tanpa akun login)'
    )

    op.create_table(
        'classes',
        sa.Column('id', sa.UUID(), nullable=False, comment='Identitas unik kelas'),
        sa.Column('course_id', sa.UUID(), nullable=False, comment='Mata kuliah yang diajarkan pada kelas ini'),
        sa.Column('section', sa.String(length=10), nullable=False, comment='Kelas/seksi (mis. A, B)'),
        sa.Column('lecturer_id', sa.UUID(), nullable=False, comment='Dosen pengampu kelas'),
        sa.Column('academic_year', sa.String(length=20), nullable=False, comment='Tahun akademik (mis. 2026/2027)'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Waktu pembuatan data kelas'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ),
        sa.ForeignKeyConstraint(['lecturer_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'section', 'academic_year', name='uq_classes_course_section_academic_year'),
        comment='Tabel kelas (seksi mata kuliah yang diampu dosen)'
    )
    op.create_index(op.f('ix_classes_course_id'), 'classes', ['course_id'], unique=False)
    op.create_index(op.f('ix_classes_lecturer_id'), 'classes', ['lecturer_id'], unique=False)

    op.create_table(
        'enrollments',
        sa.Column('id', sa.UUID(), nullable=False, comment='Identitas unik pendaftaran'),
        sa.Column('class_id', sa.UUID(), nullable=False, comment='Kelas yang diikuti mahasiswa'),
        sa.Column('student_id', sa.UUID(), nullable=False, comment='Mahasiswa yang terdaftar pada kelas'),
        sa.Column('enrolled_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='Waktu mahasiswa terdaftar pada kelas'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'student_id', name='uq_enrollments_class_student'),
        comment='Tabel pendaftaran mahasiswa pada kelas'
    )
    op.create_index(op.f('ix_enrollments_class_id'), 'enrollments', ['class_id'], unique=False)
    op.create_index(op.f('ix_enrollments_student_id'), 'enrollments', ['student_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_enrollments_student_id'), table_name='enrollments')
    op.drop_index(op.f('ix_enrollments_class_id'), table_name='enrollments')
    op.drop_table('enrollments')
    op.drop_index(op.f('ix_classes_lecturer_id'), table_name='classes')
    op.drop_index(op.f('ix_classes_course_id'), table_name='classes')
    op.drop_table('classes')
    op.drop_table('students')
