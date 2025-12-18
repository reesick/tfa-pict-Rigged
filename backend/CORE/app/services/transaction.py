"""
Transaction Service - Enhanced with soft delete, duplicate detection, and search.
Clean, straightforward CRUD operations with safety features.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import date as date_type, timedelta
from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal

from app.models.transaction import Transaction
from app.models.blockchain import UserCorrection
from app.utils.exceptions import NotFoundException


class TransactionService:
    """Transaction service with duplicate detection, soft delete, and search."""
    
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
        description: Optional[str] = None,
        check_duplicate: bool = True
    ) -> Transaction:
        """
        Create a new transaction with optional duplicate detection.
        
        Duplicate criteria: same date, similar amount (±5%), similar merchant.
        """
        # Check for duplicate if enabled
        if check_duplicate:
            duplicate = self.find_duplicate(
                user_id=user_id,
                amount=amount,
                transaction_date=transaction_date,
                merchant_raw=merchant_raw
            )
            if duplicate:
                # Return existing instead of creating duplicate
                return duplicate
        
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
        """Get single transaction by ID. Excludes soft-deleted."""
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
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
        max_amount: Optional[float] = None,
        search: Optional[str] = None,
        include_deleted: bool = False
    ) -> Tuple[List[Transaction], int]:
        """
        List transactions with filters and full-text search.
        
        Args:
            search: Search in merchant_raw and description
            include_deleted: If True, includes soft-deleted transactions
        """
        # Base query - exclude deleted by default
        query = self.db.query(Transaction).filter(Transaction.user_id == user_id)
        
        if not include_deleted:
            query = query.filter(Transaction.is_deleted == False)
        
        # Apply filters
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
        
        # Full-text search in merchant_raw and description
        if search and len(search) >= 2:
            search_pattern = f"%{search.lower()}%"
            query = query.filter(or_(
                func.lower(Transaction.merchant_raw).like(search_pattern),
                func.lower(Transaction.description).like(search_pattern)
            ))
        
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
        """Update transaction fields."""
        transaction = self.get_by_id(transaction_id, user_id)
        
        for field, value in updates.items():
            if value is not None and hasattr(transaction, field):
                if field == 'amount':
                    value = Decimal(str(value))
                setattr(transaction, field, value)
        
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    # ==================== DELETE ====================
    def delete(self, transaction_id: UUID, user_id: UUID, hard_delete: bool = False) -> None:
        """
        Delete a transaction.
        
        Args:
            hard_delete: If True, permanently deletes. If False (default), soft deletes.
        """
        transaction = self.get_by_id(transaction_id, user_id)
        
        if hard_delete:
            self.db.delete(transaction)
        else:
            # Soft delete - just flag it
            transaction.is_deleted = True
        
        self.db.commit()
    
    def restore(self, transaction_id: UUID, user_id: UUID) -> Transaction:
        """Restore a soft-deleted transaction."""
        # Get including deleted
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not transaction:
            raise NotFoundException(detail="Transaction not found")
        
        transaction.is_deleted = False
        self.db.commit()
        self.db.refresh(transaction)
        return transaction
    
    # ==================== DUPLICATE DETECTION ====================
    def find_duplicate(
        self,
        user_id: UUID,
        amount: float,
        transaction_date: date_type,
        merchant_raw: Optional[str] = None,
        tolerance_percent: float = 5.0
    ) -> Optional[Transaction]:
        """
        Find potential duplicate transaction.
        
        Criteria:
        - Same user
        - Same date (±1 day)
        - Similar amount (±tolerance_percent)
        - Similar merchant (if provided)
        """
        amount_decimal = Decimal(str(amount))
        tolerance = amount_decimal * Decimal(str(tolerance_percent / 100))
        min_amount = amount_decimal - tolerance
        max_amount = amount_decimal + tolerance
        
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False,
            Transaction.date.between(
                transaction_date - timedelta(days=1),
                transaction_date + timedelta(days=1)
            ),
            Transaction.amount.between(min_amount, max_amount)
        )
        
        # If merchant provided, try to match
        if merchant_raw:
            merchant_lower = merchant_raw.lower()[:20]  # First 20 chars
            query = query.filter(
                func.lower(Transaction.merchant_raw).like(f"%{merchant_lower}%")
            )
        
        return query.first()
    
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
        
        old_value = str(getattr(transaction, field, ""))
        
        if field == 'amount':
            setattr(transaction, field, Decimal(new_value))
        else:
            setattr(transaction, field, new_value)
        
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
        """Get basic transaction statistics. Excludes soft-deleted."""
        
        query = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        )
        
        count = query.count()
        
        if count == 0:
            return {
                "total_transactions": 0,
                "total_amount": "0.00",
                "average_amount": "0.00",
                "categories": {},
                "sources": {}
            }
        
        total = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        ).scalar() or Decimal("0")
        
        average = total / count if count > 0 else Decimal("0")
        
        category_stats = self.db.query(
            Transaction.category,
            func.count(Transaction.id),
            func.sum(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        ).group_by(Transaction.category).all()
        
        categories = {}
        for cat, cnt, amt in category_stats:
            categories[cat or "Uncategorized"] = {
                "count": cnt,
                "amount": str(amt or 0)
            }
        
        source_stats = self.db.query(
            Transaction.source,
            func.count(Transaction.id)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.is_deleted == False
        ).group_by(Transaction.source).all()
        
        sources = {src: cnt for src, cnt in source_stats}
        
        return {
            "total_transactions": count,
            "total_amount": f"{total:.2f}",
            "average_amount": f"{average:.2f}",
            "categories": categories,
            "sources": sources
        }
