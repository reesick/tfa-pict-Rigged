"""
WebSocket Message Type Standards - Pydantic Schemas
All WebSocket messages must follow these formats for Person 2/3/4 integration.
"""
from enum import Enum
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class MessageType(str, Enum):
    """Standard message types for WebSocket communication."""
    
    # Connection
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    PONG = "pong"
    
    # Transactions
    TRANSACTION_CREATED = "transaction_created"
    TRANSACTION_UPDATED = "transaction_updated"
    TRANSACTION_DELETED = "transaction_deleted"
    NEW_TRANSACTION = "new_transaction"
    
    # Budgets
    BUDGET_ALERT = "budget_alert"
    BUDGET_UPDATED = "budget_updated"
    
    # ML/AI (Person 2)
    ANOMALY_DETECTED = "anomaly_detected"
    ANOMALY_ALERT = "anomaly_alert"
    SUBSCRIPTION_DETECTED = "subscription_detected"
    SUBSCRIPTION_REMINDER = "subscription_reminder"
    
    # Blockchain (Person 3)
    BLOCKCHAIN_ANCHORED = "blockchain_anchored"
    BLOCKCHAIN_VERIFIED = "blockchain_verified"
    
    # Portfolio
    PORTFOLIO_UPDATE = "portfolio_update"


class WebSocketMessage(BaseModel):
    """Base WebSocket message format - ALL messages use this."""
    type: str  # MessageType value
    data: Dict[str, Any]
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


# ==================== MESSAGE FACTORIES ====================
# These create properly formatted messages for each type

def msg_connected(user_id: str) -> dict:
    """Create connection confirmation message."""
    return WebSocketMessage(
        type=MessageType.CONNECTED,
        data={"message": "WebSocket connected", "user_id": user_id}
    ).model_dump()


def msg_budget_alert(
    category: str,
    spent: float,
    limit: float,
    percentage: float
) -> dict:
    """Create budget alert message."""
    return WebSocketMessage(
        type=MessageType.BUDGET_ALERT,
        data={
            "category": category,
            "spent": spent,
            "limit": limit,
            "percentage": round(percentage, 1),
            "message": f"You've spent {percentage:.1f}% of your {category} budget"
        }
    ).model_dump()


def msg_transaction_created(transaction_data: dict) -> dict:
    """Create transaction created message."""
    return WebSocketMessage(
        type=MessageType.TRANSACTION_CREATED,
        data=transaction_data
    ).model_dump()


def msg_transaction_updated(transaction_data: dict) -> dict:
    """Create transaction updated message."""
    return WebSocketMessage(
        type=MessageType.TRANSACTION_UPDATED,
        data=transaction_data
    ).model_dump()


def msg_anomaly_detected(
    transaction_id: str,
    anomaly_score: float,
    reason: str
) -> dict:
    """
    Create anomaly detection message.
    
    Person 2 Usage:
        from app.websocket.message_types import msg_anomaly_detected
        message = msg_anomaly_detected(txn_id, 0.92, "Unusual amount")
        await manager.send_to_user(user_id, message)
    """
    return WebSocketMessage(
        type=MessageType.ANOMALY_DETECTED,
        data={
            "transaction_id": transaction_id,
            "anomaly_score": round(anomaly_score, 4),
            "reason": reason,
            "severity": "high" if anomaly_score > 0.8 else "medium" if anomaly_score > 0.5 else "low"
        }
    ).model_dump()


def msg_subscription_detected(
    merchant: str,
    amount: float,
    period_days: int,
    next_date: str,
    confidence: float
) -> dict:
    """
    Create subscription detection message.
    
    Person 2 Usage:
        from app.websocket.message_types import msg_subscription_detected
        message = msg_subscription_detected("Netflix", 15.99, 30, "2024-01-15", 0.95)
        await manager.send_to_user(user_id, message)
    """
    period_label = "monthly" if period_days >= 28 else "weekly" if period_days >= 7 else f"every {period_days} days"
    return WebSocketMessage(
        type=MessageType.SUBSCRIPTION_DETECTED,
        data={
            "merchant": merchant,
            "amount": amount,
            "period_days": period_days,
            "period_label": period_label,
            "next_expected_date": next_date,
            "confidence": round(confidence, 2),
            "message": f"Detected {period_label} subscription: {merchant} - ${amount}"
        }
    ).model_dump()


def msg_blockchain_anchored(
    transaction_id: str,
    blockchain_hash: str,
    ipfs_cid: Optional[str] = None
) -> dict:
    """
    Create blockchain anchoring confirmation.
    
    Person 3 Usage:
        from app.websocket.message_types import msg_blockchain_anchored
        message = msg_blockchain_anchored(txn_id, "0x123...", "Qm123...")
        await manager.send_to_user(user_id, message)
    """
    return WebSocketMessage(
        type=MessageType.BLOCKCHAIN_ANCHORED,
        data={
            "transaction_id": transaction_id,
            "blockchain_hash": blockchain_hash,
            "ipfs_cid": ipfs_cid,
            "message": "Transaction anchored to blockchain"
        }
    ).model_dump()


def msg_subscription_reminder(
    merchant: str,
    amount: float,
    expected_date: str
) -> dict:
    """Create subscription reminder message."""
    return WebSocketMessage(
        type=MessageType.SUBSCRIPTION_REMINDER,
        data={
            "merchant": merchant,
            "expected_amount": amount,
            "expected_date": expected_date,
            "message": f"Upcoming payment: {merchant} - ${amount} on {expected_date}"
        }
    ).model_dump()


def msg_error(error_message: str, code: Optional[str] = None) -> dict:
    """Create error message."""
    return WebSocketMessage(
        type=MessageType.ERROR,
        data={"error": error_message, "code": code}
    ).model_dump()
