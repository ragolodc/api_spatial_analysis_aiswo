"""Celery application bootstrap for async workers."""

from celery import Celery

from src.shared.config import settings

celery_app = Celery(
    "aiswo_spatial",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.conf.update(
    task_default_queue=settings.profile_analysis_queue,
    task_routes={
        "src.shared.workers.tasks.profile_analysis_tasks.generate_zone_profiles": {
            "queue": settings.profile_analysis_queue,
        }
    },
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
)

celery_app.conf.include = [
    "src.shared.workers.tasks.profile_analysis_tasks",
]
