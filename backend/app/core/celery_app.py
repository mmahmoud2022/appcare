"""
Celery application configuration for asynchronous tasks and scheduled jobs
"""
from celery import Celery
from celery.schedules import crontab

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Initialize Celery app
celery_app = Celery(
    "sante_medical",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",  # France timezone
    enable_utc=False,
    
    # Task execution
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # 4 minutes soft limit
    
    # Result backend
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Send appointment reminders daily at 9:00 AM
        "send-daily-appointment-reminders": {
            "task": "app.tasks.send_daily_appointment_reminders",
            "schedule": crontab(hour=9, minute=0),  # Every day at 9:00 AM
            "options": {
                "expires": 3600,  # Task expires if not run within 1 hour
            },
        },
        
        # Clean up expired tokens every day at 2:00 AM
        "cleanup-expired-tokens": {
            "task": "app.tasks.cleanup_expired_tokens",
            "schedule": crontab(hour=2, minute=0),  # Every day at 2:00 AM
            "options": {
                "expires": 3600,
            },
        },
        
        # Optional: Clean up old appointments (soft-deleted) every week
        "cleanup-old-appointments": {
            "task": "app.tasks.cleanup_old_appointments",
            "schedule": crontab(hour=3, minute=0, day_of_week=0),  # Every Sunday at 3:00 AM
            "options": {
                "expires": 7200,
            },
        },
    },
    
    # Task routes - Uncomment to use dedicated queues
    # task_routes={
    #     "app.tasks.send_*": {"queue": "emails"},
    #     "app.tasks.cleanup_*": {"queue": "maintenance"},
    # },
)

# Auto-discover tasks from all registered apps
celery_app.autodiscover_tasks(["app.tasks"])

logger.info(f"Celery app configured with broker: {settings.REDIS_URL}")
logger.info("Beat schedule configured: daily reminders at 9:00 AM, token cleanup at 2:00 AM")
