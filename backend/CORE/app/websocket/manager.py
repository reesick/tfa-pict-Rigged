"""
WebSocket Connection Manager - Manages active connections per user.
Simple implementation for real-time notifications.
"""
from fastapi import WebSocket
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


@dataclass
class UserConnection:
    """Represents a single user's WebSocket connection."""
    user_id: str
    websocket: WebSocket
    
    async def send_json(self, data: dict):
        """Send JSON data to this connection."""
        await self.websocket.send_json(data)


class ConnectionManager:
    """
    Manages WebSocket connections for all users.
    
    Features:
    - Track multiple connections per user (multiple tabs/devices)
    - Broadcast to specific user
    - Broadcast to all users
    - Handle disconnects gracefully
    """
    
    def __init__(self):
        # user_id -> list of WebSocket connections
        self._connections: Dict[str, List[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        
        if user_id not in self._connections:
            self._connections[user_id] = []
        
        self._connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected. Total connections: {self.total_connections}")
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Remove a WebSocket connection."""
        if user_id in self._connections:
            if websocket in self._connections[user_id]:
                self._connections[user_id].remove(websocket)
            
            # Clean up empty user entries
            if not self._connections[user_id]:
                del self._connections[user_id]
        
        logger.info(f"User {user_id} disconnected. Total connections: {self.total_connections}")
    
    async def send_to_user(self, user_id: str, message: dict):
        """Send a message to all connections of a specific user."""
        if user_id not in self._connections:
            return
        
        disconnected = []
        for websocket in self._connections[user_id]:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to user {user_id}: {e}")
                disconnected.append(websocket)
        
        # Clean up disconnected sockets
        for ws in disconnected:
            self.disconnect(ws, user_id)
    
    async def broadcast(self, message: dict):
        """Send a message to all connected users."""
        for user_id in list(self._connections.keys()):
            await self.send_to_user(user_id, message)
    
    def is_connected(self, user_id: str) -> bool:
        """Check if a user has any active connections."""
        return user_id in self._connections and len(self._connections[user_id]) > 0
    
    @property
    def total_connections(self) -> int:
        """Total number of active connections."""
        return sum(len(connections) for connections in self._connections.values())
    
    @property
    def connected_users(self) -> List[str]:
        """List of connected user IDs."""
        return list(self._connections.keys())


# Global connection manager instance
manager = ConnectionManager()


# ==================== NOTIFICATION HELPERS ====================

async def notify_budget_alert(user_id: str, alert: dict):
    """Send budget alert notification to user."""
    await manager.send_to_user(user_id, {
        "type": "budget_alert",
        "data": alert
    })


async def notify_new_transaction(user_id: str, transaction: dict):
    """Send new transaction notification to user."""
    await manager.send_to_user(user_id, {
        "type": "new_transaction",
        "data": transaction
    })


async def notify_anomaly_detected(user_id: str, transaction_id: str, score: float):
    """Send anomaly detection notification to user."""
    await manager.send_to_user(user_id, {
        "type": "anomaly_detected",
        "data": {
            "transaction_id": transaction_id,
            "anomaly_score": score,
            "message": f"Unusual transaction detected (score: {score:.2f})"
        }
    })


async def notify_blockchain_anchored(user_id: str, batch_info: dict):
    """Send blockchain anchoring confirmation to user."""
    await manager.send_to_user(user_id, {
        "type": "blockchain_anchored",
        "data": batch_info
    })
