"""
Authentication API endpoints.
NOTE: Registration and login are handled by Supabase Auth (frontend).
Backend only verifies Supabase JWT tokens.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.audit_log import AuditLog
from app.schemas.auth import UserResponse, MessageResponse
from app.utils.dependencies import get_current_user
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])
settings = get_settings()


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile from Supabase JWT token"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    Authentication Flow:
    1. Frontend logs in via Supabase Auth
    2. Frontend sends JWT to this endpoint
    3. Backend verifies JWT and returns user profile
    
    Requires valid Supabase access token in Authorization header:
    `Authorization: Bearer <supabase_access_token>`
    """
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Update current user profile",
    description="Update user profile fields (not authentication data)"
)
async def update_me(
    full_name: str = None,
    phone: str = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> UserResponse:
    """
    Update current user's profile.
    
    Note: Email and password changes are handled via Supabase Auth,
    not this endpoint.
    """
    if full_name is not None:
        current_user.full_name = full_name
    if phone is not None:
        current_user.phone = phone
    
    db.commit()
    db.refresh(current_user)
    
    # Audit log
    AuditLog.log(db, "user.update", user_id=current_user.id)
    db.commit()
    
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        phone=current_user.phone,
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at
    )


@router.get(
    "/status",
    summary="Check auth status",
    description="Verify if the provided token is valid"
)
async def auth_status(
    current_user: User = Depends(get_current_user)
) -> dict:
    """
    Check if the current authentication token is valid.
    
    Returns user ID and email if authenticated.
    Useful for frontend to verify session validity.
    """
    return {
        "authenticated": True,
        "user_id": str(current_user.id),
        "email": current_user.email,
        "is_verified": current_user.is_verified
    }


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Log logout event (actual logout handled by Supabase)"
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Logout user.
    
    For Supabase Auth:
    - Frontend should call supabase.auth.signOut()
    - This endpoint logs the logout event
    
    Token invalidation is handled by Supabase.
    """
    AuditLog.log(db, "user.logout", user_id=current_user.id)
    db.commit()
    
    return MessageResponse(
        message="Logged out successfully",
        detail="Please call supabase.auth.signOut() on frontend"
    )


# ==================== SUPABASE INFO ====================

@router.get(
    "/supabase-config",
    summary="Get Supabase configuration",
    description="Returns Supabase URL and anon key for frontend"
)
async def get_supabase_config() -> dict:
    """
    Get Supabase configuration for frontend.
    
    Returns public Supabase URL and anon key (safe to expose).
    Frontend uses these to initialize Supabase client.
    """
    if not settings.supabase_url:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured"
        )
    
    return {
        "supabase_url": settings.supabase_url,
        "supabase_anon_key": settings.supabase_anon_key
    }
