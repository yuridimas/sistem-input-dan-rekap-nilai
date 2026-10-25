"""Grade-release notification audit and existing release backfill."""

from alembic import op
import sqlalchemy as sa

revision = "0007_notifications"
down_revision = "0006_rankings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.UUID(), nullable=False, comment="Identitas unik notifikasi"),
        sa.Column("grade_id", sa.UUID(), nullable=False, comment="Nilai akhir yang diberitahukan kepada mahasiswa"),
        sa.Column("student_email", sa.String(255), nullable=True, comment="Alamat email tujuan; kosong bila mahasiswa belum memiliki email"),
        sa.Column("status", sa.String(20), nullable=False, server_default="queued", comment="Status pengiriman: queued, sent, atau failed"),
        sa.Column("error_message", sa.Text(), nullable=True, comment="Pesan kegagalan pengiriman terakhir"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True, comment="Waktu notifikasi berhasil dikirim"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Waktu pembuatan notifikasi"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["grade_id"], ["grades.id"]),
        sa.CheckConstraint("status IN ('queued', 'sent', 'failed')", name="ck_notifications_status"),
        comment="Tabel status pengiriman notifikasi rilis nilai",
    )
    op.create_index("ix_notifications_grade_id", "notifications", ["grade_id"], unique=True)
    op.create_index("ix_notifications_status", "notifications", ["status"])
    op.execute("""
        INSERT INTO notifications (id, grade_id, student_email, status, sent_at)
        SELECT gen_random_uuid(), g.id, s.email,
               CASE WHEN g.release_notified_at IS NULL THEN 'queued' ELSE 'sent' END,
               g.release_notified_at
        FROM grades g JOIN enrollments e ON e.id = g.enrollment_id
        JOIN students s ON s.id = e.student_id WHERE g.status = 'finalized'
    """)


def downgrade() -> None:
    op.drop_table("notifications")
