"""
WebSocket API Endpoint - Real-time notifications with JWT auth.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from sqlalchemy.orm import Session
import logging

from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token
from app.websocket.manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


async def get_user_from_token(token: str, db: Session) -> User | None:
    """Validate JWT token and return user."""
    if not token:
        return None
    
    payload = decode_token(token)
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="JWT access token")
):
    """
    WebSocket endpoint for real-time notifications.
    
    Connect with: ws://host/ws?token=<jwt_token>
    
    Messages received will be JSON with format:
    {
        "type": "budget_alert" | "new_transaction" | "anomaly_detected" | "blockchain_anchored",
        "data": {...}
    }
    """
    # Get database session
    from app.database import SessionLocal
    db = SessionLocal()
    
    try:
        # Authenticate user
        user = await get_user_from_token(token, db)
        
        if not user:
            await websocket.close(code=4001, reason="Invalid or expired token")
            return
        
        user_id = str(user.id)
        
        # Connect
        await manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_json({
            "type": "connected",
            "data": {
                "message": "WebSocket connected successfully",
                "user_id": user_id
            }
        })
        
        try:
            # Keep connection alive and listen for messages
            while True:
                # Wait for any message (ping/pong or client commands)
                data = await websocket.receive_text()
                
                # Echo for testing (can be extended for client commands)
                if data == "ping":
                    await websocket.send_json({"type": "pong"})
                
        except WebSocketDisconnect:
            manager.disconnect(websocket, user_id)
            logger.info(f"WebSocket disconnected for user {user_id}")
            
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal error")
        except:
            pass
    finally:
        db.close()


@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status."""
    return {
        "total_connections": manager.total_connections,
        "connected_users": len(manager.connected_users)
    }
