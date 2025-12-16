"""Authentication API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.user import User
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    TokenResponse,
    TokenRefresh,
    UserResponse,
    PasswordChange,
    MessageResponse
)
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token_type
)
from app.utils.dependencies import get_current_user
from app.utils.exceptions import (
    UnauthorizedException,
    ConflictException,
    ValidationException
)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="Create a new user account and return authentication tokens"
)
def register(
    data: UserRegister,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Register a new user account.
    
    - **email**: Must be unique and valid email format
    - **password**: Minimum 8 characters
    - **full_name**: User's full name
    - **phone**: Optional phone number
    
    Returns access and refresh tokens for immediate authentication.
    """
    # Check if email already registered
    existing_user = db.query(User).filter(User.email == data.email).first()
    if existing_user:
        raise ConflictException(detail="Email already registered")
    
    # Create new user
    try:
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            phone=data.phone,
            wallet_addresses=[],
            preferences={}
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        
    except IntegrityError:
        db.rollback()
        raise ConflictException(detail="Email already registered")
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600  # 1 hour
    )


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="User login",
    description="Authenticate user with email and password"
)
def login(
    data: UserLogin,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Authenticate user and return tokens.
    
    - **email**: Registered email address
    - **password**: User password
    
    Returns access and refresh tokens upon successful authentication.
    """
    # Find user by email
    user = db.query(User).filter(User.email == data.email).first()
    
    if not user:
        raise UnauthorizedException(detail="Incorrect email or password")
    
    # Verify password
    if not verify_password(data.password, user.hashed_password):
        raise UnauthorizedException(detail="Incorrect email or password")
    
    # Check if account is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact support."
        )
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Refresh access token",
    description="Get new access token using refresh token"
)
def refresh_token(
    data: TokenRefresh,
    db: Session = Depends(get_db)
) -> TokenResponse:
    """
    Refresh access token using valid refresh token.
    
    - **refresh_token**: Valid refresh token (not expired)
    
    Returns new access and refresh tokens.
    """
    # Verify refresh token
    payload = verify_token_type(data.refresh_token, "refresh")
    
    if not payload:
        raise UnauthorizedException(detail="Invalid or expired refresh token")
    
    # Get user
    user_id = payload.get("sub")
    if not user_id:
        raise UnauthorizedException(detail="Invalid token payload")
    
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise UnauthorizedException(detail="User not found")
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    # Generate new tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get current user profile",
    description="Get authenticated user's profile information"
)
def get_me(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """
    Get current authenticated user's profile.
    
    Requires valid access token in Authorization header:
    `Authorization: Bearer <access_token>`
    
    Returns user profile information (excludes password).
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


@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change password",
    description="Change user password (requires current password)"
)
def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> MessageResponse:
    """
    Change user password.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    
    Requires authentication. Returns success message.
    """
    # Verify current password
    if not verify_password(data.current_password, current_user.hashed_password):
        raise ValidationException(detail="Current password is incorrect")
    
    # Check new password is different
    if data.current_password == data.new_password:
        raise ValidationException(detail="New password must be different from current password")
    
    # Update password
    current_user.hashed_password = hash_password(data.new_password)
    db.commit()
    
    return MessageResponse(
        message="Password changed successfully",
        detail="Please use your new password for future logins"
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Logout user",
    description="Logout current user (client-side token invalidation)"
)
def logout(
    current_user: User = Depends(get_current_user)
) -> MessageResponse:
    """
    Logout user.
    
    For JWT tokens, logout is primarily client-side (delete tokens).
    This endpoint confirms the logout action.
    
    To implement server-side logout:
    - Add token blacklist in Redis
    - Check blacklist in get_current_user dependency
    """
    return MessageResponse(
        message="Logged out successfully",
        detail="Please delete your tokens on the client side"
    )
