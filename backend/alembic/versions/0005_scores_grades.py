"""Scores and draft/finalized grades with Indonesian comments."""

from alembic import op
import sqlalchemy as sa

revision = "0005_scores_grades"
down_revision = "0004_components"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "scores",
        sa.Column("id", sa.UUID(), nullable=False, comment="Identitas unik nilai komponen"),
        sa.Column("enrollment_id", sa.UUID(), nullable=False, comment="Pendaftaran mahasiswa pemilik nilai"),
        sa.Column("component_id", sa.UUID(), nullable=False, comment="Komponen penilaian yang dinilai"),
        sa.Column("score", sa.Numeric(6, 2), nullable=False, comment="Nilai yang diperoleh mahasiswa"),
        sa.Column("entered_by", sa.UUID(), nullable=False, comment="Pengguna yang terakhir memasukkan nilai"),
        sa.Column("entered_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp(), comment="Waktu nilai pertama kali dimasukkan"),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.clock_timestamp(), comment="Waktu pembaruan nilai terakhir"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["component_id"], ["components.id"]),
        sa.ForeignKeyConstraint(["entered_by"], ["users.id"]),
        sa.UniqueConstraint("enrollment_id", "component_id", name="uq_scores_enrollment_component"),
        sa.CheckConstraint("score >= 0", name="ck_scores_nonnegative"),
        comment="Tabel nilai mahasiswa per komponen penilaian",
    )
    for column in ("enrollment_id", "component_id", "entered_by"):
        op.create_index(f"ix_scores_{column}", "scores", [column])
    op.create_table(
        "grades",
        sa.Column("id", sa.UUID(), nullable=False, comment="Identitas unik nilai akhir"),
        sa.Column("enrollment_id", sa.UUID(), nullable=False, comment="Pendaftaran mahasiswa pemilik nilai akhir"),
        sa.Column("final_score", sa.Numeric(6, 2), nullable=False, comment="Nilai akhir terbobot pada skala seratus"),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft", comment="Status nilai: draft atau finalized"),
        sa.Column("finalized_at", sa.DateTime(timezone=True), nullable=True, comment="Waktu finalisasi nilai"),
        sa.Column("finalized_by", sa.UUID(), nullable=True, comment="Pengguna yang memfinalisasi nilai"),
        sa.Column("release_notified_at", sa.DateTime(timezone=True), nullable=True, comment="Waktu notifikasi rilis nilai terkirim"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.ForeignKeyConstraint(["finalized_by"], ["users.id"]),
        sa.CheckConstraint("status IN ('draft', 'finalized')", name="ck_grades_status"),
        sa.CheckConstraint("final_score >= 0 AND final_score <= 100", name="ck_grades_final_score"),
        comment="Tabel nilai akhir dan status rilis mahasiswa",
    )
    op.create_index("ix_grades_enrollment_id", "grades", ["enrollment_id"], unique=True)
    op.create_index("ix_grades_status", "grades", ["status"])
    op.create_index("ix_grades_finalized_by", "grades", ["finalized_by"])


def downgrade() -> None:
    op.drop_table("grades")
    op.drop_table("scores")
