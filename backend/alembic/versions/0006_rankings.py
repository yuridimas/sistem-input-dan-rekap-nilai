"""Sequential class rankings with Indonesian comments."""

from alembic import op
import sqlalchemy as sa

revision = "0006_rankings"
down_revision = "0005_scores_grades"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "rankings",
        sa.Column("id", sa.UUID(), nullable=False, comment="Identitas unik peringkat"),
        sa.Column("class_id", sa.UUID(), nullable=False, comment="Kelas pemilik peringkat"),
        sa.Column("enrollment_id", sa.UUID(), nullable=False, comment="Pendaftaran mahasiswa yang diberi peringkat"),
        sa.Column("rank", sa.Integer(), nullable=False, comment="Peringkat berurutan dalam kelas"),
        sa.Column("computed_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now(), comment="Waktu penghitungan peringkat kelas"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.ForeignKeyConstraint(["enrollment_id"], ["enrollments.id"]),
        sa.UniqueConstraint("class_id", "enrollment_id", name="uq_rankings_class_enrollment"),
        sa.UniqueConstraint("class_id", "rank", name="uq_rankings_class_rank"),
        sa.CheckConstraint("rank > 0", name="ck_rankings_positive_rank"),
        comment="Tabel peringkat kelas saat nilai difinalisasi",
    )
    op.create_index("ix_rankings_class_id", "rankings", ["class_id"])
    op.create_index("ix_rankings_enrollment_id", "rankings", ["enrollment_id"])


def downgrade() -> None:
    op.drop_table("rankings")
