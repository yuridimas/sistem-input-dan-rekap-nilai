"""Grade-release publisher and email worker configuration.

Konfigurasi broker Redis bagi publisher rilis dan worker notifikasi.

Service mencatat kegagalan enqueue sendiri sehingga retry koneksi
otomatis dinonaktifkan.
"""

from celery import Celery

from app.config import get_settings

celery_app = Celery("grades", broker=get_settings().redis_url, include=["app.tasks.notifications"])
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    task_publish_retry=False,
    broker_connection_retry=False,
    broker_connection_retry_on_startup=False,
    broker_connection_max_retries=0,
    broker_connection_timeout=1,
    broker_pool_limit=0,
    # Prefetch satu membatasi task yang dipesan worker saat pengiriman SMTP lambat.
    worker_prefetch_multiplier=1,
    broker_transport_options={"socket_connect_timeout": 1, "socket_timeout": 1, "retry_on_timeout": False},
)
