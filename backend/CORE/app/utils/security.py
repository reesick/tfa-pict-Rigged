"""
Security utilities for Supabase JWT token verification.
Authentication is handled by Supabase Auth - backend only verifies tokens.
"""
import base64
import logging
from jose import JWTError, jwt
from datetime import datetime
from typing import Optional, Dict, Any
from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


def get_supabase_jwt_secret() -> str:
    """
    Get Supabase JWT secret (may be base64 encoded).
    Supabase JWT secrets are base64 encoded by default.
    """
    secret = settings.supabase_jwt_secret
    
    if not secret:
        # Fallback to legacy JWT_SECRET for backward compatibility
        return settings.jwt_secret
    
    # Supabase JWT secrets are base64 encoded
    # Try to decode if it looks like base64
    try:
        # Check if it's base64 by trying to decode
        if len(secret) > 50 and '/' in secret or '+' in secret or '=' in secret:
            decoded = base64.b64decode(secret)
            return decoded.decode('utf-8')
    except Exception:
        pass
    
    return secret


def decode_supabase_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate Supabase JWT token.
    
    Supabase tokens have structure:
    {
        "aud": "authenticated",
        "exp": 1234567890,
        "sub": "user-uuid",  # This is the user ID
        "email": "user@example.com",
        "role": "authenticated",
        ...
    }
    
    Args:
        token: JWT token from Supabase Auth
        
    Returns:
        Decoded payload if valid, None if invalid
    """
    try:
        secret = get_supabase_jwt_secret()
        
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={
                "verify_aud": False,  # Supabase uses different audiences
                "verify_iss": False   # Different issuers
            }
        )
        
        # Validate required fields
        if not payload.get("sub"):
            logger.warning("Token missing 'sub' (user ID)")
            return None
        
        # Check expiration (jose does this automatically, but log it)
        exp = payload.get("exp")
        if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
            logger.warning("Token expired")
            return None
        
        return payload
        
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error decoding token: {e}")
        return None


def get_user_id_from_token(token: str) -> Optional[str]:
    """
    Extract user ID from Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        User ID (UUID string) if valid, None otherwise
    """
    payload = decode_supabase_token(token)
    if payload:
        return payload.get("sub")
    return None


def get_user_email_from_token(token: str) -> Optional[str]:
    """
    Extract email from Supabase JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Email if present, None otherwise
    """
    payload = decode_supabase_token(token)
    if payload:
        return payload.get("email")
    return None


# ==================== LEGACY SUPPORT ====================
# These functions are kept for backward compatibility during migration
# They use the legacy JWT_SECRET (not Supabase)

from passlib.context import CryptContext

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
    bcrypt__rounds=12
)


def hash_password(password: str) -> str:
    """Hash password using bcrypt (legacy, Supabase handles auth)."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password (legacy, Supabase handles auth)."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: Dict[str, Any], expires_delta=None) -> str:
    """Create JWT token (legacy, use Supabase Auth instead)."""
    from datetime import timedelta
    
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    return jwt.encode(
        to_encode,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm
    )


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode JWT token - tries Supabase first, then legacy.
    
    This provides backward compatibility during migration.
    """
    # Try Supabase token first
    payload = decode_supabase_token(token)
    if payload:
        return payload
    
    # Fallback to legacy token format
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm]
        )
        return payload
    except JWTError:
        return None
