"""
WebSocket Connection Manager - Manages active connections per user.
Enhanced with standardized message types for Person 2/3/4 integration.
"""
from fastapi import WebSocket
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


# ==================== MESSAGE TYPES ====================
# Standardized message types for all team members

class MessageType:
    """Standard WebSocket message types for integration."""
    CONNECTED = "connected"
    TRANSACTION_UPDATE = "transaction_update"
    NEW_TRANSACTION = "new_transaction"
    BUDGET_ALERT = "budget_alert"
    ANOMALY_ALERT = "anomaly_alert"
    SUBSCRIPTION_REMINDER = "subscription_reminder"
    BLOCKCHAIN_ANCHORED = "blockchain_anchored"
    PORTFOLIO_UPDATE = "portfolio_update"
    ERROR = "error"


# ==================== CONNECTION MANAGER ====================

class ConnectionManager:
    """
    Manages WebSocket connections for all users.
    
    Features:
    - Track multiple connections per user (multiple tabs/devices)
    - Broadcast to specific user
    - Broadcast to all users
    - Handle disconnects gracefully
    
    Usage (from Person 2/3/4):
        from app.websocket.manager import notify_new_transaction, MessageType
        await notify_new_transaction(user_id, transaction_data)
    """
    
    def __init__(self):
        self._connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self._connections:
            self._connections[user_id] = []
        
        self._connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total: {self.total_connections}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self._connections:
            if websocket in self._connections[user_id]:
                self._connections[user_id].remove(websocket)
            if not self._connections[user_id]:
                del self._connections[user_id]
        
        logger.info(f"User {user_id} disconnected. Total: {self.total_connections}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user."""
        if user_id not in self._connections:
            return False
        
        # Add timestamp to all messages
        if "timestamp" not in message:
            message["timestamp"] = datetime.utcnow().isoformat()
        
        disconnected = []
        sent = False
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_json(message)
                sent = True
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                disconnected.append(websocket)
        
        for ws in disconnected:
            self.disconnect(ws, user_id)
        
        return sent
    
    async def broadcast(self, message: dict):
        """Send a message to all connected users."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._connections and len(self._connections[user_id]) > 0
    
    @property
    def total_connections(self) -> int:
        return sum(len(c) for c in self._connections.values())
    
    @property
    def connected_users(self) -> List[str]:
        return list(self._connections.keys())


# Global instance
manager = ConnectionManager()


# ==================== NOTIFICATION HELPERS ====================
# Use these functions from Person 2/3/4 code

async def notify_new_transaction(user_id: str, transaction: dict):
    """
    Send new transaction notification.
    
    Usage (Person 2):
        await notify_new_transaction(user_id, {"id": "...", "amount": 50.00})
    """
    await manager.send_to_user(user_id, {
        "type": MessageType.NEW_TRANSACTION,
        "data": transaction
    })


async def notify_transaction_update(user_id: str, transaction: dict):
    """Send transaction update (category change, correction, etc)."""
    await manager.send_to_user(user_id, {
        "type": MessageType.TRANSACTION_UPDATE,
        "data": transaction
    })


async def notify_budget_alert(user_id: str, alert: dict):
    """
    Send budget alert when threshold exceeded.
    
    alert should contain: category, limit_amount, current_spending, percentage_used
    """
    await manager.send_to_user(user_id, {
        "type": MessageType.BUDGET_ALERT,
        "data": alert
    })


async def notify_anomaly_detected(user_id: str, transaction_id: str, score: float):
    """
    Send anomaly detection alert.
    
    Usage (Person 2 ML):
        await notify_anomaly_detected(user_id, txn_id, 0.85)
    """
    await manager.send_to_user(user_id, {
        "type": MessageType.ANOMALY_ALERT,
        "data": {
            "transaction_id": transaction_id,
            "anomaly_score": score,
            "message": f"Unusual transaction detected (score: {score:.2f})"
        }
    })


async def notify_subscription_reminder(user_id: str, subscription: dict):
    """
    Send subscription/recurring payment reminder.
    
    Usage (Person 2 ML):
        await notify_subscription_reminder(user_id, {
            "merchant": "Netflix",
            "expected_amount": 15.99,
            "expected_date": "2024-01-15"
        })
    """
    await manager.send_to_user(user_id, {
        "type": MessageType.SUBSCRIPTION_REMINDER,
        "data": subscription
    })


async def notify_blockchain_anchored(user_id: str, batch_info: dict):
    """
    Send blockchain anchoring confirmation.
    
    Usage (Person 3):
        await notify_blockchain_anchored(user_id, {
            "batch_id": "...",
            "merkle_root": "0x...",
            "tx_hash": "0x..."
        })
    """
    await manager.send_to_user(user_id, {
        "type": MessageType.BLOCKCHAIN_ANCHORED,
        "data": batch_info
    })


async def notify_portfolio_update(user_id: str, portfolio: dict):
    """Send portfolio value change notification."""
    await manager.send_to_user(user_id, {
        "type": MessageType.PORTFOLIO_UPDATE,
        "data": portfolio
    })
