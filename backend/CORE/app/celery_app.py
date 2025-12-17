"""
Celery Application Configuration
Background task processing for ML, notifications, and blockchain.
"""
import os
from celery import Celery

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "smartfinance",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        "app.tasks.process_transaction",
        "app.tasks.notifications",
        "app.tasks.blockchain",
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task result expiration (1 hour)
    result_expires=3600,
    
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_annotations={
        "*": {"rate_limit": "100/s"}
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
)

# Beat schedule for periodic tasks
celery_app.conf.beat_schedule = {
    # Check budget alerts every hour
    "check-budget-alerts": {
        "task": "app.tasks.notifications.check_all_budget_alerts",
        "schedule": 3600.0,  # Every hour
    },
    # Process pending blockchain batches every 5 minutes
    "process-blockchain-batches": {
        "task": "app.tasks.blockchain.process_pending_batches",
        "schedule": 300.0,  # Every 5 minutes
    },
}
