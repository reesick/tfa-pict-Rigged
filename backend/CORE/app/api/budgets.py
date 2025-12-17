"""
Budget API Endpoints - CRUD and alerts.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.budget import (
    BudgetCreate,
    BudgetUpdate,
    BudgetResponse,
    BudgetListResponse,
    BudgetAlert
)
from app.services.budget import BudgetService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])


# ==================== LIST ====================
@router.get("/", response_model=BudgetListResponse, summary="List budgets")
def list_budgets(
    active_only: bool = Query(default=True, description="Only show active budgets"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets for current user with spending info."""
    service = BudgetService(db)
    budgets = service.list_all(current_user.id, active_only=active_only)
    
    # Add spending calculations
    data = [service.get_budget_with_spending(b) for b in budgets]
    
    return BudgetListResponse(data=data, total=len(data))


# ==================== ALERTS ====================
@router.get("/alerts", response_model=list[BudgetAlert], summary="Get budget alerts")
def get_budget_alerts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all budgets that have exceeded their alert threshold."""
    service = BudgetService(db)
    return service.get_alerts(current_user.id)


# ==================== GET ONE ====================
@router.get("/{budget_id}", response_model=BudgetResponse, summary="Get budget")
def get_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single budget with spending info."""
    service = BudgetService(db)
    budget = service.get_by_id(budget_id, current_user.id)
    return service.get_budget_with_spending(budget)


# ==================== CREATE ====================
@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED, summary="Create budget")
def create_budget(
    data: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new budget."""
    service = BudgetService(db)
    budget = service.create(
        user_id=current_user.id,
        category=data.category,
        limit_amount=data.limit_amount,
        period=data.period,
        start_date=data.start_date,
        end_date=data.end_date,
        alert_threshold=data.alert_threshold
    )
    return service.get_budget_with_spending(budget)


# ==================== UPDATE ====================
@router.patch("/{budget_id}", response_model=BudgetResponse, summary="Update budget")
def update_budget(
    budget_id: UUID,
    data: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a budget."""
    service = BudgetService(db)
    
    updates = {}
    if data.limit_amount is not None:
        updates['limit_amount'] = data.limit_amount
    if data.alert_threshold is not None:
        updates['alert_threshold'] = data.alert_threshold
    if data.end_date is not None:
        updates['end_date'] = data.end_date
    if data.is_active is not None:
        updates['is_active'] = data.is_active
    
    budget = service.update(budget_id, current_user.id, **updates)
    return service.get_budget_with_spending(budget)


# ==================== DELETE ====================
@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete budget")
def delete_budget(
    budget_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a budget."""
    service = BudgetService(db)
    service.delete(budget_id, current_user.id)
