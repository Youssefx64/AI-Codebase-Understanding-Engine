"""Celery application factory.

Celery is used for offloading heavy analysis tasks so the API remains
responsive. The broker and backend default to Redis; configure via
CELERY_BROKER_URL and CELERY_RESULT_BACKEND environment variables.
"""

from celery import Celery

from core.config import get_settings


def create_celery_app() -> Celery:
    """Create and configure the Celery application."""
    settings = get_settings()

    app = Celery(
        "codebase_engine",
        broker=settings.celery_broker_url,
        backend=settings.celery_result_backend,
        include=["workers.tasks"],
    )

    app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        task_track_started=True,
        task_acks_late=True,
        worker_prefetch_multiplier=1,
        result_expires=3600,
        task_routes={
            "workers.tasks.run_analysis_pipeline": {"queue": "analysis"},
            "workers.tasks.generate_embeddings": {"queue": "embeddings"},
        },
    )

    return app


celery_app = create_celery_app()
