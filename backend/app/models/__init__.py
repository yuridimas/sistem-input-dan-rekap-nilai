"""SQLAlchemy declarative models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


from app.models.user import User  # noqa: E402

__all__ = ["Base", "User"]