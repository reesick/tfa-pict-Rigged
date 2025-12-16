"""Budget model - User budget tracking and alerts."""
from sqlalchemy import Column, String, Date, Numeric, ForeignKey, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base


class Budget(Base):
    """
    User budget allocation model.
    
    Stores budget limits for categories with date ranges.
    Used for spending tracking and alert generation.
    """
    __tablename__ = "budgets"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique budget identifier"
    )
    
    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Budget owner"
    )
    
    # Budget Configuration
    category = Column(
        String(100),
        nullable=False,
        comment="Budget category (must match transaction categories)"
    )
    amount = Column(
        Numeric(12, 2),
        nullable=False,
        comment="Budget limit amount"
    )
    
    # Date Range
    start_date = Column(
        Date,
        nullable=False,
        comment="Budget period start date"
    )
    end_date = Column(
        Date,
        nullable=False,
        comment="Budget period end date"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="budgets",
        doc="Budget owner"
    )
    
    # Constraints and Indexes
    __table_args__ = (
        # One budget per user per category (upsert pattern)
        UniqueConstraint('user_id', 'category', name='uq_user_category'),
        
        # Query budgets by user and category
        Index('idx_budget_user_category', 'user_id', 'category'),
        
        # Find active budgets
        Index('idx_budget_dates', 'start_date', 'end_date'),
    )
    
    def __repr__(self):
        return f"<Budget(id={self.id}, user_id={self.user_id}, category={self.category}, amount={self.amount})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "category": self.category,
            "amount": float(self.amount) if self.amount else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None
        }
    
    def is_active(self, check_date=None) -> bool:
        """
        Check if budget is currently active.
        
        Args:
            check_date: Date to check (defaults to today)
            
        Returns:
            True if budget period includes check_date
        """
        from datetime import date
        check_date = check_date or date.today()
        return self.start_date <= check_date <= self.end_date
