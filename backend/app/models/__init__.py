"""SQLAlchemy declarative models."""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base class for all ORM models."""


from app.models.class_ import Class  # noqa: E402
from app.models.component import Component  # noqa: E402
from app.models.course import Course  # noqa: E402
from app.models.enrollment import Enrollment  # noqa: E402
from app.models.grade import Grade  # noqa: E402
from app.models.ranking import Ranking  # noqa: E402
from app.models.score import Score  # noqa: E402
from app.models.student import Student  # noqa: E402
from app.models.user import User  # noqa: E402

__all__ = ["Base", "Class", "Component", "Course", "Enrollment", "Grade", "Ranking", "Score", "Student", "User"]
