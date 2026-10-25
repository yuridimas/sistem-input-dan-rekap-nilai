"""Administrator delivery audit responses."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationStatus


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    grade_id: uuid.UUID
    student_email: str | None
    status: NotificationStatus
    error_message: str | None
    sent_at: datetime | None
    created_at: datetime
