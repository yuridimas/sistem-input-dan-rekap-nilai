"""Guard notification publication results against superseded retries."""

from alembic import op
import sqlalchemy as sa

revision = "0008_notification_dispatch"
down_revision = "0007_notifications"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column(
        "dispatch_token", sa.UUID(), nullable=False, server_default=sa.func.gen_random_uuid(),
        comment="Token pengantrean untuk mengabaikan hasil percobaan yang sudah digantikan",
    ))


def downgrade() -> None:
    op.drop_column("notifications", "dispatch_token")
