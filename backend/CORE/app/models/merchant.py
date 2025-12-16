"""Merchant Master model - Canonical merchant database for fuzzy matching."""
from sqlalchemy import Column, String, Index, ARRAY, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class MerchantMaster(Base):
    """
    Canonical merchant database.
    
    Stores canonical merchant names with aliases for fuzzy matching.
    Person 2 uses this for merchant normalization and matching.
    """
    __tablename__ = "merchant_master"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique merchant identifier"
    )
    
    # Merchant Information
    canonical_name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="Official merchant name (single source of truth)"
    )
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Primary category: Food & Dining, Shopping, Transport, etc."
    )
    country = Column(
        String(2),
        nullable=True,
        index=True,
        comment="ISO 3166-1 alpha-2 country code (IN, US, UK, etc.)"
    )
    
    # Fuzzy Matching Data (Person 2)
    aliases = Column(
        ARRAY(String),
        default=list,
        nullable=False,
        comment="Array of merchant name variants for fuzzy matching: ['SWGY', 'Swiggy', 'Swiggy Bangalore']"
    )
    
    # Additional Metadata
    tags = Column(
        JSONB,
        default=dict,
        nullable=False,
        comment="Flexible metadata: {type: 'restaurant', cuisine: 'indian', chain: true, vegan_options: true}"
    )
    logo_url = Column(
        String(512),
        nullable=True,
        comment="Merchant logo URL for UI display"
    )
    website = Column(
        String(512),
        nullable=True,
        comment="Official merchant website"
    )
    
    # Statistics (updated by background jobs)
    transaction_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Total number of transactions linked to this merchant"
    )
    
    # Relationships
    transactions = relationship(
        "Transaction",
        foreign_keys="Transaction.merchant_id",
        back_populates="merchant",
        lazy="dynamic",
        doc="Transactions linked to this merchant"
    )
    
    # Indexes for Performance
    __table_args__ = (
        # GIN index for fast array contains queries (fuzzy matching)
        Index('idx_merchant_aliases_gin', 'aliases', postgresql_using='gin'),
        
        # Category filtering
        Index('idx_merchant_category', 'category'),
        
        # Country filtering
        Index('idx_merchant_country', 'country'),
        
        # Name search
        Index('idx_merchant_name', 'canonical_name'),
        
        # JSONB tags search
        Index('idx_merchant_tags_gin', 'tags', postgresql_using='gin'),
        
        # Popular merchants (for autocomplete)
        Index('idx_merchant_popular', 'transaction_count', postgresql_ops={'transaction_count': 'DESC'}),
    )
    
    def __repr__(self):
        return f"<MerchantMaster(id={self.id}, name={self.canonical_name}, category={self.category})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "canonical_name": self.canonical_name,
            "category": self.category,
            "country": self.country,
            "aliases": self.aliases,
            "tags": self.tags,
            "logo_url": self.logo_url,
            "website": self.website,
            "transaction_count": self.transaction_count
        }
    
    def add_alias(self, alias: str) -> None:
        """
        Add a new alias to the merchant.
        
        Args:
            alias: Merchant name variant to add
        """
        if alias and alias not in self.aliases:
            if self.aliases is None:
                self.aliases = []
            self.aliases = self.aliases + [alias]  # PostgreSQL ARRAY append
    
    def matches_text(self, text: str) -> bool:
        """
        Check if text matches this merchant (exact match on aliases).
        
        Args:
            text: Normalized merchant text to match
            
        Returns:
            True if text is in aliases or canonical name
        """
        text_lower = text.lower().strip()
        if text_lower == self.canonical_name.lower():
            return True
        return any(alias.lower() == text_lower for alias in (self.aliases or []))
