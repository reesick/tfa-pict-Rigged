"""User model - Core user accounts and authentication."""
from sqlalchemy import Column, String, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class User(Base):
    """
    User account model.
    
    Stores user authentication credentials, profile information,
    blockchain wallet addresses, and user preferences.
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
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
        comment="Phone number with country code"
    )
    full_name = Column(
        String(255),
        nullable=True,
        comment="User's full name"
    )
    
    # Blockchain Integration (Person 3)
    wallet_addresses = Column(
        JSONB,
        default=list,
        nullable=False,
        comment="Array of blockchain wallet addresses: ['0x123...', '0x456...']"
    )
    
    # User Preferences
    preferences = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="User settings: {currency: 'USD', theme: 'dark', language: 'en'}"
    )
    
    # Status Flags
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Account active status (false = deactivated)"
    )
    is_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Email verification status"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Account creation timestamp"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    transactions = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="User's financial transactions"
    )
    budgets = relationship(
        "Budget",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="User's budget allocations"
    )
    portfolios = relationship(
        "PortfolioHolding",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="User's investment holdings"
    )
    corrections = relationship(
        "UserCorrection",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="User's transaction corrections (ML training data)"
    )
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_users_email', 'email'),
        Index('idx_users_active', 'is_active', postgresql_where=is_active),
        Index('idx_users_wallet_gin', 'wallet_addresses', postgresql_using='gin'),
        Index('idx_users_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email})>"
    
    def to_dict(self):
        """Convert model to dictionary (excludes password)."""
        return {
            "id": str(self.id),
            "email": self.email,
            "phone": self.phone,
            "full_name": self.full_name,
            "wallet_addresses": self.wallet_addresses,
            "preferences": self.preferences,
            "is_active": self.is_active,
            "is_verified": self.is_verified,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
