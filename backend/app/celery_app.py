"""Minimal grade-release publisher; email workers are introduced in Task 13."""

from celery import Celery

from app.config import get_settings

celery_app = Celery("grades", broker=get_settings().redis_url)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_publish_retry=False,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=0,
    broker_connection_timeout=1,
    broker_pool_limit=0,
    broker_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1, "retry_on_timeout": False},
)
