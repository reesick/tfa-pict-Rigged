"""
Transaction Model - Financial transactions with full audit trail.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Date, Text, Index, Enum, ForeignKey
from sqlalchemy.orm import relationship
import uuid
import json
import enum
from datetime import datetime, date
from decimal import Decimal
from app.database import Base


# ==================== CUSTOM TYPES ====================

class GUID(str):
    """String-based UUID type that works with both PostgreSQL and SQLite."""
    pass


from sqlalchemy import TypeDecorator

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
            if isinstance(value, str):
                return uuid.UUID(value)
            return value
        return value


class JSONType(TypeDecorator):
    """Platform-independent JSON type."""
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


# ==================== ENUMS ====================

class TransactionSource(str, enum.Enum):
    """How the transaction was created/imported."""
    OCR = "ocr"           # Receipt image scanning
    SMS = "sms"           # Bank SMS parsing
    CSV = "csv"           # Bank statement import
    MANUAL = "manual"     # User manual entry
    BLOCKCHAIN = "blockchain"  # On-chain sync


# ==================== TRANSACTION MODEL ====================

class Transaction(Base):
    """
    Financial transaction model.
    
    Handles:
    - Transaction amounts with decimal precision
    - Multiple data sources (OCR, SMS, CSV, manual, blockchain)
    - AI confidence scores for extracted data
    - Blockchain anchoring status
    
    Edge cases handled:
    - Decimal precision for currency
    - NULL handling for optional fields
    - Cascading deletes for corrections
    - Proper indexing for queries
    """
    __tablename__ = "transactions"
    
    # Primary Key
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique transaction identifier"
    )
    
    # Foreign Key
    user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    # Core Transaction Data
    amount = Column(
        Numeric(18, 4),  # High precision for crypto/financial
        nullable=False,
        comment="Transaction amount with 4 decimal precision"
    )
    date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Transaction date"
    )
    
    # Merchant Information
    merchant_raw = Column(
        String(500),
        nullable=True,
        comment="Raw merchant text from source (receipt/SMS)"
    )
    merchant_id = Column(
        GUIDType(),
        ForeignKey("merchant_master.id", ondelete="SET NULL"),
        nullable=True,
        comment="Matched merchant from master list"
    )
    
    # Categorization
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Transaction category (Food, Transport, etc.)"
    )
    subcategory = Column(
        String(100),
        nullable=True,
        comment="Sub-category (e.g., Coffee under Food)"
    )
    description = Column(
        Text,
        nullable=True,
        comment="User notes or additional description"
    )
    
    # Data Source
    source = Column(
        String(20),
        default="manual",
        nullable=False,
        comment="Data source: ocr, sms, csv, manual"
    )
    ingestion_id = Column(
        GUIDType(),
        nullable=True,
        comment="Batch import ID for CSV/bulk imports"
    )
    
    # AI Confidence Scores
    confidence = Column(
        JSONType(),
        nullable=True,
        comment="AI extraction confidence: {amount: 0.95, merchant: 0.87}"
    )
    
    # Anomaly Detection
    anomaly_score = Column(
        Numeric(5, 4),  # 0.0000 to 9.9999
        default=0.0,
        comment="Anomaly detection score (0=normal, 1=anomaly)"
    )
    
    # Blockchain Anchoring (Person 3)
    blockchain_hash = Column(
        String(66),
        nullable=True,
        unique=True,
        comment="Merkle root hash on blockchain"
    )
    ipfs_cid = Column(
        String(200),
        nullable=True,
        comment="IPFS CID for receipt image"
    )
    is_anchored = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether transaction is blockchain-anchored"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When transaction was created in system"
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last modification timestamp"
    )
    
    # Soft Delete
    is_deleted = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Soft delete flag - True hides from queries"
    )
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    merchant = relationship("MerchantMaster", back_populates="transactions")
    corrections = relationship("UserCorrection", back_populates="transaction", cascade="all, delete-orphan")
    
    # Indexes for common queries
    __table_args__ = (
        Index("idx_transactions_user_date", user_id, date.desc()),
        Index("idx_transactions_category", category),
        Index("idx_transactions_source", source),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, date={self.date})>"
    
    # ==================== HELPER METHODS ====================
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "amount": str(self.amount),
            "date": self.date.isoformat() if self.date else None,
            "merchant_raw": self.merchant_raw,
            "category": self.category,
            "description": self.description,
            "source": self.source,
            "confidence": self.confidence,
            "anomaly_score": float(self.anomaly_score) if self.anomaly_score else 0.0,
            "is_anchored": self.is_anchored,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
    
    @property
    def amount_float(self) -> float:
        """Get amount as float for calculations."""
        return float(self.amount) if self.amount else 0.0
    
    def set_confidence(self, field: str, score: float):
        """Set confidence score for a field (0.0 to 1.0)."""
        if not self.confidence:
            self.confidence = {}
        if 0.0 <= score <= 1.0:
            self.confidence[field] = score
        else:
            raise ValueError(f"Confidence score must be between 0 and 1, got {score}")
    
    def mark_anchored(self, blockchain_hash: str, ipfs_cid: str = None):
        """Mark transaction as blockchain-anchored."""
        self.blockchain_hash = blockchain_hash
        if ipfs_cid:
            self.ipfs_cid = ipfs_cid
        self.is_anchored = True
