"""Pydantic schemas for authentication requests and responses."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime


class UserRegister(BaseModel):
    """Schema for user registration request."""
    
    email: EmailStr = Field(
        ...,
        description="User email address (must be unique)",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (minimum 8 characters)",
        examples=["SecurePass123!"]
    )
    full_name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="User's full name",
        examples=["John Doe"]
    )
    phone: Optional[str] = Field(
        None,
        max_length=20,
        description="Phone number with country code",
        examples=["+1234567890"]
    )


class UserLogin(BaseModel):
    """Schema for user login request."""
    
    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"]
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["SecurePass123!"]
    )


class TokenResponse(BaseModel):
    """Schema for token response (login/register)."""
    
    access_token: str = Field(
        ...,
        description="JWT access token (expires in 1 hour)"
    )
    refresh_token: str = Field(
        ...,
        description="JWT refresh token (expires in 30 days)"
    )
    token_type: str = Field(
        default="bearer",
        description="Token type (always 'bearer')"
    )
    expires_in: int = Field(
        default=3600,
        description="Access token expiration in seconds"
    )


class TokenRefresh(BaseModel):
    """Schema for refresh token request."""
    
    refresh_token: str = Field(
        ...,
        description="Valid refresh token"
    )


class UserResponse(BaseModel):
    """Schema for user profile response."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str = Field(
        ...,
        description="User UUID"
    )
    email: str = Field(
        ...,
        description="User email address"
    )
    full_name: Optional[str] = Field(
        None,
        description="User's full name"
    )
    phone: Optional[str] = Field(
        None,
        description="Phone number"
    )
    is_active: bool = Field(
        ...,
        description="Whether account is active"
    )
    is_verified: bool = Field(
        ...,
        description="Whether email is verified"
    )
    created_at: datetime = Field(
        ...,
        description="Account creation timestamp"
    )
    updated_at: datetime = Field(
        ...,
        description="Last update timestamp"
    )


class PasswordChange(BaseModel):
    """Schema for password change request."""
    
    current_password: str = Field(
        ...,
        description="Current password for verification"
    )
    new_password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="New password (minimum 8 characters)"
    )


class PasswordReset(BaseModel):
    """Schema for password reset request."""
    
    email: EmailStr = Field(
        ...,
        description="Email address to send reset link"
    )


class EmailVerification(BaseModel):
    """Schema for email verification."""
    
    token: str = Field(
        ...,
        description="Email verification token"
    )


class MessageResponse(BaseModel):
    """Generic message response schema."""
    
    message: str = Field(
        ...,
        description="Response message"
    )
    detail: Optional[str] = Field(
        None,
        description="Additional details"
    )
