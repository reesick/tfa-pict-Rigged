"""
Celery Application Configuration
Background task processing for ML, notifications, and blockchain.
"""
import os
from celery import Celery
from kombu import Queue

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
        "app.tasks.budgets",
    ]
)

# ==================== TASK QUEUES ====================
# Priority-based queue routing for different task types

celery_app.conf.task_queues = (
    Queue('high_priority', routing_key='high'),    # OCR, urgent tasks
    Queue('default', routing_key='default'),        # Normal tasks
    Queue('low_priority', routing_key='low'),       # Batch jobs
    Queue('scheduled', routing_key='scheduled'),    # Blockchain, reports
)

celery_app.conf.task_routes = {
    # High priority: Person 2 OCR tasks (need fast response)
    'app.tasks.process_transaction.process_new_transaction': {'queue': 'high_priority'},
    
    # Default: Normal notifications
    'app.tasks.notifications.*': {'queue': 'default'},
    
    # Low priority: Batch operations
    'app.tasks.process_transaction.batch_process_csv': {'queue': 'low_priority'},
    'app.tasks.process_transaction.update_anomaly_scores': {'queue': 'low_priority'},
    
    # Scheduled: Blockchain anchoring (can wait)
    'app.tasks.blockchain.*': {'queue': 'scheduled'},
}

celery_app.conf.task_default_queue = 'default'

# ==================== GENERAL CONFIG ====================

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
    task_max_retries=3,
    
    task_annotations={
        '*': {'rate_limit': '100/s'},
        'app.tasks.process_transaction.process_new_transaction': {'rate_limit': '50/s'},
    },
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_concurrency=4,
)

# ==================== BEAT SCHEDULE ====================
# Periodic tasks (run with: celery -A app.celery_app beat)

celery_app.conf.beat_schedule = {
    # Check budget alerts every hour
    'check-budget-alerts-hourly': {
        'task': 'app.tasks.budgets.check_all_budget_alerts',
        'schedule': 3600.0,  # Every hour
    },
    # Process pending blockchain batches every 5 minutes
    'process-blockchain-batches': {
        'task': 'app.tasks.blockchain.process_pending_batches',
        'schedule': 300.0,  # Every 5 minutes
    },
    # Detect subscription patterns nightly (Person 2)
    'detect-subscriptions-nightly': {
        'task': 'app.tasks.process_transaction.detect_subscriptions',
        'schedule': 86400.0,  # Every 24 hours
        'options': {'queue': 'low_priority'}
    },
}


# ==================== WORKER COMMANDS ====================
# 
# Start workers by queue:
#   celery -A app.celery_app worker -Q high_priority -n worker_high@%h
#   celery -A app.celery_app worker -Q default,low_priority -n worker_default@%h
#   celery -A app.celery_app worker -Q scheduled -n worker_scheduled@%h
#
# Start all queues in one worker (development):
#   celery -A app.celery_app worker -Q high_priority,default,low_priority,scheduled
#
# Start beat scheduler:
#   celery -A app.celery_app beat --loglevel=info
#
# Monitor with Flower:
#   celery -A app.celery_app flower --port=5555
