"""SQLAlchemy declarative models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


from app.models.course import Course  # noqa: E402
from app.models.user import User  # noqa: E402

__all__ = ["Base", "Course", "User"]