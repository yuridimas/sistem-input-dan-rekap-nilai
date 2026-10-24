"""Grade components with Indonesian comments.

Revision ID: 0004_components
Revises: 0003_classes_students
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_components"
down_revision = "0003_classes_students"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "components",
        sa.Column("id", sa.UUID(), nullable=False, comment="Identitas unik komponen penilaian"),
        sa.Column("class_id", sa.UUID(), nullable=False, comment="Kelas pemilik komponen penilaian"),
        sa.Column("name", sa.String(100), nullable=False, comment="Nama komponen penilaian"),
        sa.Column("category", sa.String(20), nullable=False, comment="Kategori: tugas, uts, uas, atau custom"),
        sa.Column("weight", sa.Numeric(5, 2), nullable=False, comment="Bobot komponen dalam persen"),
        sa.Column("max_score", sa.Numeric(6, 2), nullable=False, server_default="100", comment="Nilai maksimum komponen"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0", comment="Urutan tampilan komponen"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), comment="Waktu pembuatan komponen penilaian"),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"]),
        sa.CheckConstraint("weight > 0 AND weight <= 100", name="ck_components_weight"),
        sa.CheckConstraint("max_score > 0", name="ck_components_max_score"),
        sa.CheckConstraint("category IN ('tugas', 'uts', 'uas', 'custom')", name="ck_components_category"),
        comment="Tabel komponen penilaian per kelas",
    )
    op.create_index("ix_components_class_id", "components", ["class_id"])


def downgrade() -> None:
    op.drop_index("ix_components_class_id", table_name="components")
    op.drop_table("components")
