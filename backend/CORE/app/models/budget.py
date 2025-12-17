"""
Budget Model - User spending budgets and limits.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Boolean, Numeric, Date, Index, ForeignKey, TypeDecorator
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


class Budget(Base):
    """
    User budget for spending limits per category.
    
    Allows users to set monthly/weekly/custom period budgets
    per category and track spending against limits.
    """
    __tablename__ = "budgets"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique budget identifier"
    )
    
    user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    # Budget Configuration
    category = Column(
        String(100),
        nullable=False,
        comment="Budget category (e.g., Food, Transport)"
    )
    limit_amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Budget limit amount"
    )
    period = Column(
        String(20),
        default="monthly",
        nullable=False,
        comment="Budget period: daily, weekly, monthly, yearly"
    )
    
    # Period Dates
    start_date = Column(
        Date,
        nullable=False,
        comment="Budget period start date"
    )
    end_date = Column(
        Date,
        nullable=True,
        comment="Budget period end date (null = ongoing)"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether budget is currently active"
    )
    
    # Notifications
    alert_threshold = Column(
        Numeric(5, 2),
        default=80.0,
        comment="Alert when spending reaches this percentage"
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
    user = relationship("User", back_populates="budgets")
    
    __table_args__ = (
        Index("idx_budget_user_category", user_id, category),
        Index("idx_budget_active", is_active),
    )
    
    def __repr__(self):
        return f"<Budget(id={self.id}, category={self.category}, limit={self.limit_amount})>"
