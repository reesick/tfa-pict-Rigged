"""
Recurrence Model - Subscription/recurring transaction tracking.
For Person 2 ML prediction of subscription patterns.
"""
from sqlalchemy import Column, String, DateTime, Integer, Numeric, Date, ForeignKey, Index, TypeDecorator
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


class Recurrence(Base):
    """
    Tracks detected recurring transactions (subscriptions).
    
    Person 2's ML system detects patterns and creates these records.
    Used to predict upcoming bills and notify users.
    """
    __tablename__ = "recurrences"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique recurrence identifier"
    )
    
    user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    merchant_id = Column(
        GUIDType(),
        ForeignKey("merchant_master.id", ondelete="SET NULL"),
        nullable=True,
        comment="Linked merchant (if identified)"
    )
    
    # Pattern Information
    description = Column(
        String(255),
        nullable=True,
        comment="Description (e.g., 'Netflix Subscription')"
    )
    
    amount_mean = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Average transaction amount"
    )
    
    amount_std = Column(
        Numeric(12, 2),
        default=0,
        comment="Standard deviation of amount"
    )
    
    period_days = Column(
        Integer,
        nullable=False,
        comment="Days between occurrences (7=weekly, 30=monthly)"
    )
    
    # Prediction
    next_expected_date = Column(
        Date,
        nullable=True,
        comment="Next predicted transaction date"
    )
    
    last_occurrence = Column(
        Date,
        nullable=True,
        comment="Last observed transaction date"
    )
    
    occurrence_count = Column(
        Integer,
        default=0,
        comment="Number of times this pattern occurred"
    )
    
    # ML Confidence
    confidence = Column(
        Numeric(5, 4),
        default=0.0,
        comment="ML confidence score (0.0-1.0)"
    )
    
    # Status
    is_active = Column(
        String(10),
        default="active",
        comment="active, paused, cancelled"
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
    
    __table_args__ = (
        Index("idx_recurrence_user", user_id),
        Index("idx_recurrence_next_date", next_expected_date),
        Index("idx_recurrence_merchant", merchant_id),
    )
    
    def __repr__(self):
        return f"<Recurrence(id={self.id}, desc={self.description}, period={self.period_days}d)>"
