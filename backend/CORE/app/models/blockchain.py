"""
Blockchain Models - Merkle batches and user corrections.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Integer, Text, Index, ForeignKey, TypeDecorator
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


class MerkleBatch(Base):
    """
    Merkle tree batch for blockchain anchoring.
    
    Groups multiple transactions into a Merkle tree
    and anchors the root hash on blockchain.
    """
    __tablename__ = "merkle_batches"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique batch identifier"
    )
    
    # Merkle Data
    merkle_root = Column(
        String(66),
        nullable=False,
        unique=True,
        comment="Merkle root hash (0x...)"
    )
    transaction_count = Column(
        Integer,
        nullable=False,
        comment="Number of transactions in batch"
    )
    
    # Transaction IDs (stored as JSON array)
    transaction_ids = Column(
        Text,
        nullable=False,
        comment="JSON array of transaction UUIDs in batch"
    )
    
    # Blockchain Data
    blockchain_tx_hash = Column(
        String(66),
        nullable=True,
        comment="Blockchain transaction hash"
    )
    block_number = Column(
        Integer,
        nullable=True,
        comment="Block number containing the anchor"
    )
    chain_id = Column(
        Integer,
        default=1,
        comment="Blockchain chain ID (1=Ethereum mainnet)"
    )
    
    # Status
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="Status: pending, submitted, confirmed, failed"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    anchored_at = Column(
        DateTime,
        nullable=True,
        comment="When batch was confirmed on chain"
    )
    
    __table_args__ = (
        Index("idx_merkle_root", merkle_root),
        Index("idx_merkle_status", status),
    )
    
    def __repr__(self):
        return f"<MerkleBatch(id={self.id}, root={self.merkle_root[:10]}..., count={self.transaction_count})>"


class UserCorrection(Base):
    """
    User corrections for ML training feedback.
    
    When users correct AI-extracted data, we record it
    for Person 2's ML model improvement.
    """
    __tablename__ = "user_corrections"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique correction identifier"
    )
    
    # Foreign Keys
    user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User who made correction"
    )
    transaction_id = Column(
        GUIDType(),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Corrected transaction"
    )
    
    # Correction Data
    field_corrected = Column(
        String(50),
        nullable=False,
        comment="Field that was corrected: category, merchant, amount, date"
    )
    old_value = Column(
        String(255),
        nullable=True,
        comment="Original AI-extracted value"
    )
    new_value = Column(
        String(255),
        nullable=False,
        comment="User-corrected value"
    )
    correction_reason = Column(
        String(255),
        nullable=True,
        comment="Optional reason for correction"
    )
    
    # ML Training Status
    is_used_for_training = Column(
        Integer,
        default=0,
        comment="Whether used in ML training (0=no, 1=yes)"
    )
    
    # Timestamp
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    user = relationship("User", back_populates="corrections")
    transaction = relationship("Transaction", back_populates="corrections")
    
    __table_args__ = (
        Index("idx_correction_user", user_id),
        Index("idx_correction_transaction", transaction_id),
        Index("idx_correction_field", field_corrected),
    )
    
    def __repr__(self):
        return f"<UserCorrection(id={self.id}, field={self.field_corrected})>"
