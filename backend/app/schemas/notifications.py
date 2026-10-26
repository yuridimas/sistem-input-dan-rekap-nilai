"""Administrator delivery audit responses.

Respons audit/retry administratif untuk router notifications.

Batas field pada schema menjaga input; aturan relasi dan otorisasi tetap
berada di service.
"""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationStatus


class NotificationRead(BaseModel):
    """Status pengiriman dengan error dan waktu terkirim opsional."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    grade_id: uuid.UUID
    student_email: str | None
    status: NotificationStatus
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
