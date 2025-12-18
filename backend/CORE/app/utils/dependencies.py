"""
FastAPI dependencies for Supabase JWT authentication.
Handles token verification and user sync from Supabase Auth.
"""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token, decode_supabase_token
from app.utils.exceptions import UnauthorizedException

logger = logging.getLogger(__name__)
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT token (Supabase or legacy) and return current user.
    
    If user doesn't exist in database (first login via Supabase),
    creates the user record automatically.
    
    Flow:
    1. Frontend authenticates via Supabase Auth
    2. Frontend sends JWT token to backend
    3. Backend verifies token with Supabase JWT secret
    4. Backend creates/retrieves user record
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        User object
        
    Raises:
        UnauthorizedException: If token is invalid or expired
    """
    token = credentials.credentials
    
    # Decode and verify token (tries Supabase first, then legacy)
    payload = decode_token(token)
    
    if not payload:
        raise UnauthorizedException(detail="Invalid or expired access token")
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload - missing user ID")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    # If user doesn't exist, create from Supabase token data
    if not user:
        logger.info(f"Creating user from Supabase token: {user_id}")
        user = User(
            id=user_id,
            email=payload.get("email"),
            full_name=payload.get("user_metadata", {}).get("full_name"),
            is_active=True,
            is_verified=payload.get("email_confirmed_at") is not None,
            wallet_addresses=[],
            preferences={},
            user_metadata={"synced_from": "supabase_auth"}
        )
        db.add(user)
        try:
            db.commit()
            db.refresh(user)
            logger.info(f"User created: {user.email}")
        except Exception as e:
            db.rollback()
            logger.error(f"Error creating user: {e}")
            # Try to fetch again in case of race condition
            user = db.query(User).filter(User.id == user_id).first()
            if not user:
                raise UnauthorizedException(detail="Failed to sync user from Supabase")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user ensuring they are active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current user ensuring email is verified."""
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )
    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, None otherwise.
    Use for endpoints that work with or without authentication.
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None
