"""
Celery Application Configuration
Конфигурация асинхронной очереди задач
"""
from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "financial_analysis",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.file_processing_tasks"]  # Import tasks
)

# Configure Celery
celery_app.conf.update(
    task_track_started=settings.CELERY_TASK_TRACK_STARTED,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,

    # Result expiration
    result_expires=3600,  # 1 hour
)

# Optional: Task routes for different queues
celery_app.conf.task_routes = {
    "app.tasks.file_processing_tasks.process_file_task": {"queue": "file_processing"},
    "app.tasks.file_processing_tasks.ml_analysis_task": {"queue": "ml_analysis"},  # Rule-based fraud analysis (name kept for backward compatibility)
}
