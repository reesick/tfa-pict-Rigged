"""
Budget Service - Simple business logic for budget management.
Calculates spending and generates alerts.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date as date_type, timedelta
from typing import Optional, List, Tuple
from uuid import UUID
from decimal import Decimal

from app.models.budget import Budget
from app.models.transaction import Transaction
from app.utils.exceptions import NotFoundException


class BudgetService:
    """Simple budget service with clear methods."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CREATE ====================
    def create(
        self,
        user_id: UUID,
        category: str,
        limit_amount: float,
        start_date: date_type,
        period: str = "monthly",
        end_date: Optional[date_type] = None,
        alert_threshold: float = 80.0
    ) -> Budget:
        """Create a new budget."""
        budget = Budget(
            user_id=user_id,
            category=category,
            limit_amount=Decimal(str(limit_amount)),
            period=period,
            start_date=start_date,
            end_date=end_date,
            alert_threshold=Decimal(str(alert_threshold)),
            is_active=True
        )
        self.db.add(budget)
        self.db.commit()
        self.db.refresh(budget)
        return budget
    
    # ==================== READ ====================
    def get_by_id(self, budget_id: UUID, user_id: UUID) -> Budget:
        """Get budget by ID. Raises NotFoundException if not found."""
        budget = self.db.query(Budget).filter(
            Budget.id == budget_id,
            Budget.user_id == user_id
        ).first()
        
        if not budget:
            raise NotFoundException(detail="Budget not found")
        
        return budget
    
    def list_all(self, user_id: UUID, active_only: bool = True) -> List[Budget]:
        """List all budgets for a user."""
        query = self.db.query(Budget).filter(Budget.user_id == user_id)
        
        if active_only:
            query = query.filter(Budget.is_active == True)
        
        return query.order_by(Budget.category).all()
    
    # ==================== UPDATE ====================
    def update(self, budget_id: UUID, user_id: UUID, **updates) -> Budget:
        """Update budget fields."""
        budget = self.get_by_id(budget_id, user_id)
        
        for field, value in updates.items():
            if value is not None and hasattr(budget, field):
                if field in ('limit_amount', 'alert_threshold'):
                    value = Decimal(str(value))
                setattr(budget, field, value)
        
        self.db.commit()
        self.db.refresh(budget)
        return budget
    
    # ==================== DELETE ====================
    def delete(self, budget_id: UUID, user_id: UUID) -> None:
        """Delete a budget."""
        budget = self.get_by_id(budget_id, user_id)
        self.db.delete(budget)
        self.db.commit()
    
    # ==================== SPENDING CALCULATIONS ====================
    def get_spending(self, user_id: UUID, category: str, start_date: date_type, end_date: Optional[date_type] = None) -> Decimal:
        """Calculate total spending for a category within date range."""
        query = self.db.query(func.sum(Transaction.amount)).filter(
            Transaction.user_id == user_id,
            Transaction.category == category,
            Transaction.date >= start_date
        )
        
        if end_date:
            query = query.filter(Transaction.date <= end_date)
        
        result = query.scalar()
        return result or Decimal("0")
    
    def get_budget_with_spending(self, budget: Budget) -> dict:
        """Get budget with current spending calculated."""
        # Calculate period end if not set
        end = budget.end_date
        if not end:
            # Calculate based on period
            if budget.period == "daily":
                end = budget.start_date
            elif budget.period == "weekly":
                end = budget.start_date + timedelta(days=6)
            elif budget.period == "monthly":
                # Add roughly a month
                end = budget.start_date + timedelta(days=30)
            elif budget.period == "yearly":
                end = budget.start_date + timedelta(days=365)
            else:
                end = date_type.today()
        
        # Calculate spending
        spending = self.get_spending(
            budget.user_id,
            budget.category,
            budget.start_date,
            end
        )
        
        limit = float(budget.limit_amount)
        spent = float(spending)
        percentage = (spent / limit * 100) if limit > 0 else 0
        
        return {
            "id": str(budget.id),
            "user_id": str(budget.user_id),
            "category": budget.category,
            "limit_amount": f"{budget.limit_amount:.2f}",
            "period": budget.period,
            "start_date": budget.start_date,
            "end_date": budget.end_date,
            "is_active": budget.is_active,
            "alert_threshold": float(budget.alert_threshold),
            "current_spending": f"{spending:.2f}",
            "percentage_used": round(percentage, 2),
            "is_over_limit": percentage >= 100
        }
    
    # ==================== ALERTS ====================
    def get_alerts(self, user_id: UUID) -> List[dict]:
        """Get all budgets that have exceeded their alert threshold."""
        budgets = self.list_all(user_id, active_only=True)
        alerts = []
        
        for budget in budgets:
            info = self.get_budget_with_spending(budget)
            threshold = float(budget.alert_threshold)
            
            if info["percentage_used"] >= threshold:
                alerts.append({
                    "budget_id": info["id"],
                    "category": info["category"],
                    "limit_amount": info["limit_amount"],
                    "current_spending": info["current_spending"],
                    "percentage_used": info["percentage_used"],
                    "alert_threshold": threshold,
                    "message": f"{info['category']} budget at {info['percentage_used']:.1f}% ({info['current_spending']} of {info['limit_amount']})"
                })
        
        return alerts
