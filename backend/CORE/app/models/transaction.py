"""Transaction model - Core financial transaction data."""
from sqlalchemy import (
    Column, String, DateTime, Numeric, Date, 
    ForeignKey, Enum, Float, Text, Index, Boolean
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base
import enum


class TransactionSource(str, enum.Enum):
    """Transaction data source types."""
    OCR = "ocr"
    SMS = "sms"
    CSV = "csv"
    MANUAL = "manual"
    BLOCKCHAIN = "blockchain"


class Transaction(Base):
    """
    Financial transaction model.
    
    Stores all user transactions with AI/ML metadata, blockchain
    anchoring information, and source tracking for Person 2's ingestion system.
    """
    __tablename__ = "transactions"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique transaction identifier"
    )
    
    # Foreign Keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner of this transaction"
    )
    merchant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("merchant_master.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Linked canonical merchant (null if not matched)"
    )
    
    # Core Transaction Data
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Transaction amount (exact decimal, supports up to 9,999,999,999.99)"
    )
    date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Transaction date (day-level precision)"
    )
    merchant_raw = Column(
        Text,
        nullable=True,
        comment="Raw merchant text extracted from OCR/SMS before normalization"
    )
    category = Column(
        String(100),
        nullable=True,
        index=True,
        comment="Transaction category (Food, Transport, Shopping, etc.)"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Optional transaction notes/description"
    )
    
    # Source Metadata
    source = Column(
        Enum(TransactionSource),
        nullable=False,
        index=True,
        comment="How transaction was ingested: ocr, sms, csv, manual, blockchain"
    )
    ingestion_id = Column(
        UUID(as_uuid=True),
        nullable=True,
        comment="Link to Person 2's ingestion tracking record"
    )
    
    # AI/ML Data (Person 2)
    confidence = Column(
        JSONB,
        nullable=True,
        comment="AI confidence scores: {overall: 0.95, amount: 0.98, merchant: 0.92, category: 0.91}"
    )
    anomaly_score = Column(
        Float,
        default=0.0,
        nullable=False,
        index=True,
        comment="Anomaly detection score (0.0-1.0, higher = more suspicious)"
    )
    ai_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional AI/ML metadata from Person 2"
    )
    
    # Blockchain Data (Person 3)
    blockchain_hash = Column(
        String(64),
        nullable=True,
        unique=True,
        comment="SHA-256 hash of transaction for blockchain anchoring"
    )
    ipfs_cid = Column(
        String(100),
        nullable=True,
        comment="IPFS CID for receipt image storage"
    )
    is_anchored = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether transaction is anchored to blockchain"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Transaction creation timestamp (when added to system)"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="transactions",
        doc="Transaction owner"
    )
    merchant = relationship(
        "MerchantMaster",
        foreign_keys=[merchant_id],
        doc="Canonical merchant if matched"
    )
    corrections = relationship(
        "UserCorrection",
        back_populates="transaction",
        cascade="all, delete-orphan",
        lazy="dynamic",
        doc="User corrections for this transaction (ML training)"
    )
    
    # Composite Indexes for Performance
    __table_args__ = (
        # Dashboard query: Recent transactions for user
        Index('idx_txn_user_date', 'user_id', 'date', postgresql_ops={'date': 'DESC'}),
        
        # Budget tracking: User's spending by category
        Index('idx_txn_user_category', 'user_id', 'category'),
        
        # Anomaly detection: High-risk transactions
        Index('idx_txn_anomaly', 'anomaly_score', postgresql_where="anomaly_score > 0.5"),
        
        # Source filtering
        Index('idx_txn_source', 'source'),
        
        # Recent transactions timeline
        Index('idx_txn_created', 'created_at', postgresql_ops={'created_at': 'DESC'}),
        
        # Merchant analytics
        Index('idx_txn_merchant', 'merchant_id'),
        
        # JSONB confidence queries
        Index('idx_txn_confidence_gin', 'confidence', postgresql_using='gin'),
        
        # Blockchain anchoring status
        Index('idx_txn_anchored', 'is_anchored', postgresql_where="is_anchored = false"),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, date={self.date}, category={self.category})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "merchant_id": str(self.merchant_id) if self.merchant_id else None,
            "amount": float(self.amount) if self.amount else None,
            "date": self.date.isoformat() if self.date else None,
            "merchant_raw": self.merchant_raw,
            "merchant": self.merchant.to_dict() if self.merchant else None,
            "category": self.category,
            "description": self.description,
            "source": self.source.value if self.source else None,
            "ingestion_id": str(self.ingestion_id) if self.ingestion_id else None,
            "confidence": self.confidence,
            "anomaly_score": self.anomaly_score,
            "blockchain_hash": self.blockchain_hash,
            "ipfs_cid": self.ipfs_cid,
            "is_anchored": self.is_anchored,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
