"""
Budget Schemas - Simple and clear request/response schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date
from decimal import Decimal


# ==================== REQUEST SCHEMAS ====================

class BudgetCreate(BaseModel):
    """Create a new budget."""
    category: str = Field(..., max_length=100, description="Budget category")
    limit_amount: float = Field(..., gt=0, description="Budget limit")
    period: str = Field(default="monthly", description="daily, weekly, monthly, yearly")
    start_date: date = Field(..., description="Budget start date")
    end_date: Optional[date] = Field(default=None, description="End date (null=ongoing)")
    alert_threshold: float = Field(default=80.0, ge=0, le=100, description="Alert when % spent")


class BudgetUpdate(BaseModel):
    """Update a budget (all fields optional)."""
    limit_amount: Optional[float] = Field(default=None, gt=0)
    alert_threshold: Optional[float] = Field(default=None, ge=0, le=100)
    end_date: Optional[date] = Field(default=None)
    is_active: Optional[bool] = Field(default=None)


# ==================== RESPONSE SCHEMAS ====================

class BudgetResponse(BaseModel):
    """Single budget response with spending info."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    category: str
    limit_amount: str  # String for precision
    period: str
    start_date: date
    end_date: Optional[date] = None
    is_active: bool
    alert_threshold: float
    
    # Calculated fields
    current_spending: str = "0.00"
    percentage_used: float = 0.0
    is_over_limit: bool = False


class BudgetListResponse(BaseModel):
    """List of budgets."""
    data: List[BudgetResponse]
    total: int


class BudgetAlert(BaseModel):
    """Budget alert when threshold exceeded."""
    budget_id: str
    category: str
    limit_amount: str
    current_spending: str
    percentage_used: float
    alert_threshold: float
    message: str
