"""
Budget Tasks - Automated budget checking for Celery Beat.
Runs hourly to check all user budgets and send alerts.
"""
from celery import shared_task
from sqlalchemy import func
from decimal import Decimal
import logging
import asyncio

logger = logging.getLogger(__name__)


def run_async(coro):
    """Helper to run async code in sync Celery task."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task
def check_all_budget_alerts():
    """
    Check budget alerts for ALL users.
    Runs hourly via Celery Beat.
    
    Flow:
    1. Get all active budgets
    2. Calculate spending for each
    3. If over threshold, send WebSocket notification
    4. Log results
    """
    from app.database import SessionLocal
    from app.models.budget import Budget
    from app.models.transaction import Transaction
    from app.models.user import User
    from app.websocket.manager import manager
    from app.websocket.message_types import msg_budget_alert
    
    db = SessionLocal()
    alerts_sent = 0
    
    try:
        # Get all active users with budgets
        users_with_budgets = db.query(User.id).join(Budget).filter(
            User.is_active == True,
            Budget.is_active == True
        ).distinct().all()
        
        logger.info(f"Checking budgets for {len(users_with_budgets)} users")
        
        for (user_id,) in users_with_budgets:
            # Get user's active budgets
            budgets = db.query(Budget).filter(
                Budget.user_id == user_id,
                Budget.is_active == True
            ).all()
            
            for budget in budgets:
                try:
                    # Calculate spending in budget period
                    query = db.query(func.sum(Transaction.amount)).filter(
                        Transaction.user_id == user_id,
                        Transaction.category == budget.category,
                        Transaction.date >= budget.start_date
                    )
                    if budget.end_date:
                        query = query.filter(Transaction.date <= budget.end_date)
                    
                    spent = query.scalar() or Decimal('0.00')
                    percentage = float((spent / budget.limit_amount) * 100) if budget.limit_amount > 0 else 0
                    
                    # Check threshold
                    if percentage >= float(budget.alert_threshold or 80):
                        logger.info(f"Alert: User {user_id} {budget.category} at {percentage:.1f}%")
                        
                        # Send WebSocket notification (async)
                        if manager.is_connected(str(user_id)):
                            message = msg_budget_alert(
                                category=budget.category,
                                spent=float(spent),
                                limit=float(budget.limit_amount),
                                percentage=percentage
                            )
                            run_async(manager.send_to_user(str(user_id), message))
                            alerts_sent += 1
                        
                except Exception as e:
                    logger.error(f"Error checking budget {budget.id}: {e}")
                    continue
        
        logger.info(f"Budget check complete. Alerts sent: {alerts_sent}")
        return {"status": "completed", "users_checked": len(users_with_budgets), "alerts_sent": alerts_sent}
        
    except Exception as e:
        logger.error(f"Budget check task failed: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        db.close()


@shared_task
def check_user_budgets(user_id: str):
    """
    Check all budgets for a specific user.
    Called after bulk operations or on demand.
    """
    from app.database import SessionLocal
    from app.models.budget import Budget
    from app.models.transaction import Transaction
    from app.websocket.manager import manager
    from app.websocket.message_types import msg_budget_alert
    
    db = SessionLocal()
    
    try:
        budgets = db.query(Budget).filter(
            Budget.user_id == user_id,
            Budget.is_active == True
        ).all()
        
        for budget in budgets:
            query = db.query(func.sum(Transaction.amount)).filter(
                Transaction.user_id == user_id,
                Transaction.category == budget.category,
                Transaction.date >= budget.start_date
            )
            if budget.end_date:
                query = query.filter(Transaction.date <= budget.end_date)
            
            spent = query.scalar() or Decimal('0.00')
            percentage = float((spent / budget.limit_amount) * 100) if budget.limit_amount > 0 else 0
            
            if percentage >= float(budget.alert_threshold or 80):
                if manager.is_connected(str(user_id)):
                    message = msg_budget_alert(
                        category=budget.category,
                        spent=float(spent),
                        limit=float(budget.limit_amount),
                        percentage=percentage
                    )
                    run_async(manager.send_to_user(str(user_id), message))
        
        return {"status": "completed", "budgets_checked": len(budgets)}
        
    finally:
        db.close()
