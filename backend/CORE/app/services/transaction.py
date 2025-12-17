"""
Transaction Service - Simplified Business Logic
Clean, straightforward CRUD operations with minimal complexity.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date as date_type
from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.blockchain import UserCorrection
from app.utils.exceptions import NotFoundException


class TransactionService:
    """Simple transaction service with clear, readable methods."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CREATE ====================
    def create(
        self,
        user_id: UUID,
        amount: float,
        transaction_date: date_type,
        source: str = "manual",
        merchant_raw: Optional[str] = None,
        category: Optional[str] = None,
        description: Optional[str] = None
    ) -> Transaction:
        """Create a new transaction. Simple and direct."""
        transaction = Transaction(
            user_id=user_id,
            amount=Decimal(str(amount)),
            date=transaction_date,
            source=source,
            merchant_raw=merchant_raw,
            category=category,
            description=description
        )
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    # ==================== READ ====================
    def get_by_id(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        """Get single transaction by ID. Raises NotFoundException if not found."""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise NotFoundException(detail="Transaction not found")
        
        return transaction
    
    def list_all(
        self,
        user_id: UUID,
        limit: int = 50,
        offset: int = 0,
        since: Optional[date_type] = None,
        until: Optional[date_type] = None,
        category: Optional[str] = None,
        source: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None
    ) -> Tuple[List[Transaction], int]:
        """List transactions with simple filters. Returns (transactions, total_count)."""
        
        # Start with base query
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Apply filters one by one (simple and clear)
        if since:
            query = query.filter(Transaction.date >= since)
        if until:
            query = query.filter(Transaction.date <= until)
        if category:
            query = query.filter(Transaction.category == category)
        if source:
            query = query.filter(Transaction.source == source)
        if min_amount:
            query = query.filter(Transaction.amount >= Decimal(str(min_amount)))
        if max_amount:
            query = query.filter(Transaction.amount <= Decimal(str(max_amount)))
        
        # Get total count before pagination
        total = query.count()
        
        # Apply pagination and ordering
        transactions = query.order_by(
            Transaction.date.desc()
        ).offset(offset).limit(limit).all()
        
        return transactions, total
    
    # ==================== UPDATE ====================
    def update(
        self,
        transaction_id: UUID,
        user_id: UUID,
        **updates
    ) -> Transaction:
        """Update transaction fields. Simple attribute assignment."""
        transaction = self.get_by_id(transaction_id, user_id)
        
        # Only update fields that were provided
        for field, value in updates.items():
            if value is not None and hasattr(transaction, field):
                if field == 'amount':
                    value = Decimal(str(value))
                setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    # ==================== DELETE ====================
    def delete(self, transaction_id: UUID, user_id: UUID) -> None:
        """Delete a transaction. Simple removal."""
        transaction = self.get_by_id(transaction_id, user_id)
        self.db.delete(transaction)
        self.db.commit()
    
    # ==================== CORRECTIONS (for ML) ====================
    def add_correction(
        self,
        transaction_id: UUID,
        user_id: UUID,
        field: str,
        new_value: str,
        reason: Optional[str] = None
    ) -> Tuple[Transaction, UserCorrection]:
        """Add a user correction for ML training."""
        transaction = self.get_by_id(transaction_id, user_id)
        
        # Get old value
        old_value = str(getattr(transaction, field, ""))
        
        # Update the transaction
        if field == 'amount':
            setattr(transaction, field, Decimal(new_value))
        else:
            setattr(transaction, field, new_value)
        
        # Record the correction
        correction = UserCorrection(
            user_id=user_id,
            transaction_id=transaction_id,
            field_corrected=field,
            old_value=old_value,
            new_value=new_value,
            correction_reason=reason
        )
        self.db.add(correction)
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction, correction
    
    # ==================== STATISTICS ====================
    def get_stats(self, user_id: UUID) -> dict:
        """Get basic transaction statistics. Simple aggregations."""
        
        # Get all user transactions
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        # Count and sum
        count = query.count()
        
        if count == 0:
            return {
                "total_transactions": 0,
                "total_amount": "0.00",
                "average_amount": "0.00",
                "categories": {},
                "sources": {}
            }
        
        # Calculate totals
        total = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id
        ).scalar() or Decimal("0")
        
        average = total / count if count > 0 else Decimal("0")
        
        # Group by category
        category_stats = self.db.query(
            Transaction.category,
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id
        ).group_by(Transaction.category).all()
        
        categories = {}
        for cat, cnt, amt in category_stats:
            categories[cat or "Uncategorized"] = {
                "count": cnt,
                "amount": str(amt or 0)
            }
        
        # Group by source
        source_stats = self.db.query(
            Transaction.source,
            func.count(Transaction.id)
        ).filter(
            Transaction.user_id == user_id
        ).group_by(Transaction.source).all()
        
        sources = {src: cnt for src, cnt in source_stats}
        
        return {
            "total_transactions": count,
            "total_amount": f"{total:.2f}",
            "average_amount": f"{average:.2f}",
            "categories": categories,
            "sources": sources
        }
