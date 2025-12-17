"""
Notification Tasks - WebSocket and Push Notifications
Background tasks for sending real-time notifications.
"""
from celery import shared_task
import logging
import asyncio

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync context."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task
def send_budget_alert(user_id: str, alert_data: dict):
    """
    Send budget alert notification to user.
    
    Usage:
        send_budget_alert.delay(user_id, {
            "category": "Food",
            "limit_amount": "500.00",
            "current_spending": "450.00",
            "percentage_used": 90.0
        })
    """
    from app.websocket.manager import notify_budget_alert
    
    logger.info(f"Sending budget alert to user {user_id}")
    run_async(notify_budget_alert(user_id, alert_data))
    
    return {"status": "sent", "user_id": user_id}


@shared_task
def send_transaction_notification(user_id: str, transaction_data: dict):
    """
    Send new transaction notification to user.
    
    Usage:
        send_transaction_notification.delay(user_id, {
            "id": "transaction-id",
            "amount": "50.00",
            "merchant": "Starbucks",
            "category": "Food"
        })
    """
    from app.websocket.manager import notify_new_transaction
    
    logger.info(f"Sending transaction notification to user {user_id}")
    run_async(notify_new_transaction(user_id, transaction_data))
    
    return {"status": "sent", "user_id": user_id}


@shared_task
def send_anomaly_alert(user_id: str, transaction_id: str, score: float):
    """
    Send anomaly detection alert to user.
    
    Usage:
        send_anomaly_alert.delay(user_id, transaction_id, 0.85)
    """
    from app.websocket.manager import notify_anomaly_detected
    
    logger.info(f"Sending anomaly alert to user {user_id}")
    run_async(notify_anomaly_detected(user_id, transaction_id, score))
    
    return {"status": "sent", "user_id": user_id}


@shared_task
def check_all_budget_alerts():
    """
    Periodic task: Check all users' budgets for alerts.
    
    Scheduled to run every hour via Celery Beat.
    """
    logger.info("Checking all budget alerts (periodic task)")
    
    # TODO: Implement full budget check
    # 1. Get all active budgets
    # 2. Calculate spending for each
    # 3. Send alerts for those over threshold
    
    return {"status": "completed"}
