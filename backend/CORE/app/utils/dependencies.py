"""FastAPI dependencies for authentication and authorization."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token, verify_token_type
from app.utils.exceptions import UnauthorizedException

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Validate JWT access token and return current authenticated user.
    
    Used as a dependency in protected routes:
    
    Example:
        @router.get("/profile")
        def get_profile(current_user: User = Depends(get_current_user)):
            return {"email": current_user.email}
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        db: Database session
        
    Returns:
        User object of authenticated user
        
    Raises:
        UnauthorizedException: If token is invalid, expired, or user not found
    """
    token = credentials.credentials
    
    # Decode and verify token
    payload = verify_token_type(token, "access")
    
    if not payload:
        raise UnauthorizedException(detail="Invalid or expired access token")
    
    # Extract user ID from token
    user_id: str = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload")
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise UnauthorizedException(detail="User not found")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they are active.
    
    This is an additional layer of protection for sensitive operations.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object if active
        
    Raises:
        HTTPException: If user account is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


async def get_current_verified_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify email is verified.
    
    Use for operations that require email verification.
    
    Args:
        current_user: User from get_current_user dependency
        
    Returns:
        User object if verified
        
    Raises:
        HTTPException: If email not verified
    """
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
    
    Args:
        credentials: Optional HTTP Bearer token
        db: Database session
        
    Returns:
        User object if authenticated, None if not
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = verify_token_type(token, "access")
    
    if not payload:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    user = db.query(User).filter(User.id == user_id).first()
    return user if user and user.is_active else None
