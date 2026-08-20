from celery import Celery
from core.config import settings

celery_app = Celery(
    "enterprise_rag",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["workers.tasks.document_processing"]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
    worker_prefetch_multiplier=1 # For heavy tasks
)
