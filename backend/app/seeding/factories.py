"""SQLAlchemy model factories. Persistence stays in the dataset transaction."""

from faker import Faker
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory

from app.models.class_ import Class
from app.models.component import Component
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.grade import Grade
from app.models.notification import Notification
from app.models.ranking import Ranking
from app.models.score import Score
from app.models.student import Student
from app.models.user import User


def make_factory(model, seed: int):
    """Create an isolated SQLAlchemy factory with deterministic Faker locale."""
    class ModelFactory(SQLAlchemyFactory[model]):
        __faker__ = Faker(locale="id_ID")
        __random_seed__ = seed
        __check_model__ = False
        __set_relationships__ = False

    return ModelFactory


FACTORY_MODELS = (User, Course, Class, Student, Component, Enrollment, Score, Grade, Ranking, Notification)
