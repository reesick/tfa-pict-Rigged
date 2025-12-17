"""
MerchantMaster Model - Canonical merchant list for categorization.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Text, Index, TypeDecorator
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class GUIDType(TypeDecorator):
    """Platform-independent GUID type."""
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


class MerchantMaster(Base):
    """
    Master list of known merchants for transaction categorization.
    
    Used by Person 2's ML system to match raw merchant text
    to canonical merchant names and categories.
    """
    __tablename__ = "merchant_master"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique merchant identifier"
    )
    
    # Canonical Name
    canonical_name = Column(
        String(255),
        nullable=False,
        unique=True,
        comment="Standardized merchant name (e.g., 'Starbucks')"
    )
    
    # Alternative Names (for matching)
    aliases = Column(
        Text,
        nullable=True,
        comment="JSON array of aliases: ['STARBUCKS COFFEE', 'SBUX']"
    )
    
    # Categorization
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Primary category (Food, Transport, etc.)"
    )
    subcategory = Column(
        String(100),
        nullable=True,
        comment="Subcategory (Coffee, Groceries, etc.)"
    )
    
    # Metadata
    logo_url = Column(
        String(500),
        nullable=True,
        comment="URL to merchant logo"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    transactions = relationship("Transaction", back_populates="merchant")
    
    __table_args__ = (
        Index("idx_merchant_name", canonical_name),
        Index("idx_merchant_category", category),
    )
    
    def __repr__(self):
        return f"<MerchantMaster(id={self.id}, name={self.canonical_name})>"
