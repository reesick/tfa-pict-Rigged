"""
User Model - Core user accounts and authentication.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, TypeDecorator
from sqlalchemy.orm import relationship
import uuid
import json
from datetime import datetime
from app.database import Base


# ==================== CUSTOM TYPES ====================
# These types work with both PostgreSQL and SQLite

class GUID(TypeDecorator):
    """Platform-independent GUID type. Uses String(36) storage."""
    impl = String(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if isinstance(value, str) else value
        return value


class JSONType(TypeDecorator):
    """Platform-independent JSON type. Uses Text storage."""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


# ==================== USER MODEL ====================

class User(Base):
    """
    User account model.
    
    Handles:
    - Authentication (email + password)
    - Profile information
    - Blockchain wallet addresses
    - User preferences
    
    Edge cases handled:
    - Email uniqueness enforced at database level
    - Defaults for all nullable fields
    - Timestamps auto-managed
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique user identifier"
    )
    
    # Authentication
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address (unique, used for login)"
    )
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="bcrypt hashed password"
    )
    
    # Profile Information
    phone = Column(
        String(20),
        nullable=True,
        default=None,
        comment="Phone number with country code"
    )
    full_name = Column(
        String(255),
        nullable=True,
        default=None,
        comment="User's full name"
    )
    
    # Blockchain Integration
    wallet_addresses = Column(
        JSONType(),
        default=list,
        nullable=False,
        comment="Array of blockchain wallet addresses"
    )
    
    # User Preferences
    preferences = Column(
        JSONType(),
        default=dict,
        nullable=False,
        comment="User settings and preferences"
    )
    
    # Account Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether account is active"
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email is verified"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    corrections = relationship("UserCorrection", back_populates="user", cascade="all, delete-orphan")
    
    # Indexes
    __table_args__ = (
        Index("idx_users_email", email),
        Index("idx_users_active", is_active),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    # ==================== HELPER METHODS ====================
    
    def to_dict(self):
        """Convert user to dictionary (excluding password)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone": self.phone,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    def add_wallet(self, address: str) -> bool:
        """Add a wallet address if not already present."""
        if not self.wallet_addresses:
            self.wallet_addresses = []
        if address not in self.wallet_addresses:
            self.wallet_addresses = self.wallet_addresses + [address]
            return True
        return False
    
    def remove_wallet(self, address: str) -> bool:
        """Remove a wallet address if present."""
        if self.wallet_addresses and address in self.wallet_addresses:
            self.wallet_addresses = [w for w in self.wallet_addresses if w != address]
            return True
        return False
