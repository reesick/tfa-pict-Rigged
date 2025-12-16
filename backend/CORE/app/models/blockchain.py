"""Blockchain models - Merkle batching and user corrections for ML."""
from sqlalchemy import Column, String, DateTime, Date, ForeignKey, Index, Text, ARRAY, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base


class MerkleBatch(Base):
    """
    Merkle tree batch anchoring model.
    
    Person 3 uses this to batch multiple transactions into a single
    blockchain anchoring transaction for cost efficiency.
    """
    __tablename__ = "merkle_batches"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique batch identifier"
    )
    
    # Batch Information
    batch_date = Column(
        Date,
        nullable=False,
        index=True,
        comment="Date of batch creation"
    )
    transaction_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        comment="Array of transaction IDs included in this batch"
    )
    merkle_root = Column(
        String(64),
        nullable=False,
        unique=True,
        comment="Merkle tree root hash (SHA-256)"
    )
    
    # Blockchain Anchoring
    blockchain_tx_hash = Column(
        String(66),
        nullable=True,
        unique=True,
        comment="Blockchain transaction hash (0x + 64 chars for Ethereum)"
    )
    blockchain_status = Column(
        String(20),
        default="pending",
        nullable=False,
        index=True,
        comment="Anchoring status: pending, confirmed, failed"
    )
    blockchain_network = Column(
        String(50),
        default="polygon",
        nullable=False,
        comment="Blockchain network: polygon, ethereum, etc."
    )
    gas_used = Column(
        String(20),
        nullable=True,
        comment="Gas units consumed"
    )
    gas_price_gwei = Column(
        String(20),
        nullable=True,
        comment="Gas price in Gwei"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        comment="Batch creation timestamp"
    )
    confirmed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Blockchain confirmation timestamp"
    )
    
    # IPFS Storage
    ipfs_metadata_cid = Column(
        String(100),
        nullable=True,
        comment="IPFS CID for batch metadata"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_merkle_date', 'batch_date'),
        Index('idx_merkle_status', 'blockchain_status'),
        Index('idx_merkle_network', 'blockchain_network'),
    )
    
    def __repr__(self):
        return f"<MerkleBatch(id={self.id}, date={self.batch_date}, status={self.blockchain_status})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "batch_date": self.batch_date.isoformat() if self.batch_date else None,
            "transaction_ids": [str(tid) for tid in self.transaction_ids],
            "transaction_count": len(self.transaction_ids) if self.transaction_ids else 0,
            "merkle_root": self.merkle_root,
            "blockchain_tx_hash": self.blockchain_tx_hash,
            "blockchain_status": self.blockchain_status,
            "blockchain_network": self.blockchain_network,
            "gas_used": self.gas_used,
            "gas_price_gwei": self.gas_price_gwei,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "confirmed_at": self.confirmed_at.isoformat() if self.confirmed_at else None,
            "ipfs_metadata_cid": self.ipfs_metadata_cid
        }


class UserCorrection(Base):
    """
    User correction tracking model.
    
    Person 2 uses this for active learning - when users correct
    transaction categories or merchants, this data trains the ML models.
    """
    __tablename__ = "user_corrections"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique correction identifier"
    )
    
    # Foreign Keys
    transaction_id = Column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Transaction that was corrected"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who made the correction"
    )
    
    # Correction Data
    field_corrected = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Field that was corrected: category, merchant, amount, date"
    )
    old_value = Column(
        Text,
        nullable=True,
        comment="Original value before correction"
    )
    new_value = Column(
        Text,
        nullable=False,
        comment="Corrected value"
    )
    
    # ML Training Metadata
    ai_confidence_before = Column(
        Float,
        nullable=True,
        comment="AI confidence score before correction"
    )
    correction_reason = Column(
        String(255),
        nullable=True,
        comment="Optional reason for correction"
    )
    
    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Correction timestamp"
    )
    
    # Relationships
    transaction = relationship(
        "Transaction",
        back_populates="corrections",
        doc="Transaction that was corrected"
    )
    user = relationship(
        "User",
        back_populates="corrections",
        doc="User who made the correction"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_correction_user', 'user_id'),
        Index('idx_correction_transaction', 'transaction_id'),
        Index('idx_correction_field', 'field_corrected'),
        Index('idx_correction_created', 'created_at'),
    )
    
    def __repr__(self):
        return f"<UserCorrection(id={self.id}, field={self.field_corrected}, old={self.old_value}, new={self.new_value})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "transaction_id": str(self.transaction_id),
            "user_id": str(self.user_id),
            "field_corrected": self.field_corrected,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "ai_confidence_before": self.ai_confidence_before,
            "correction_reason": self.correction_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
