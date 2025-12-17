"""
Transaction Schemas - Simple and Clear
Minimal complexity, easy to understand.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any, Literal
from datetime import date, datetime


# ==================== REQUEST SCHEMAS ====================

class TransactionCreate(BaseModel):
    """Create a new transaction."""
    amount: float = Field(..., gt=0, description="Transaction amount (positive)")
    transaction_date: date = Field(..., description="Transaction date")
    merchant_raw: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)
    source: str = Field(default="manual", description="ocr, sms, csv, manual, blockchain")


class TransactionUpdate(BaseModel):
    """Update a transaction (all fields optional)."""
    amount: Optional[float] = Field(default=None, gt=0)
    transaction_date: Optional[date] = Field(default=None)
    merchant_raw: Optional[str] = Field(default=None, max_length=500)
    category: Optional[str] = Field(default=None, max_length=100)
    description: Optional[str] = Field(default=None, max_length=1000)


class TransactionCorrection(BaseModel):
    """User correction for ML training."""
    field_corrected: str = Field(..., description="Field: category, merchant, amount, date")
    new_value: str = Field(..., max_length=255)
    correction_reason: Optional[str] = Field(default=None, max_length=255)


# ==================== RESPONSE SCHEMAS ====================

class MerchantInfo(BaseModel):
    """Merchant info (optional in response)."""
    model_config = ConfigDict(from_attributes=True)
    id: str
    canonical_name: str
    category: str


class TransactionResponse(BaseModel):
    """Single transaction response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    user_id: str
    amount: str  # String for precision
    date: date
    merchant_raw: Optional[str] = None
    merchant: Optional[MerchantInfo] = None
    category: Optional[str] = None
    description: Optional[str] = None
    source: str
    confidence: Optional[Dict[str, Any]] = None
    anomaly_score: float = 0.0
    blockchain_hash: Optional[str] = None
    ipfs_cid: Optional[str] = None
    is_anchored: bool = False
    created_at: datetime
    updated_at: datetime


class TransactionListResponse(BaseModel):
    """Paginated list of transactions."""
    data: List[TransactionResponse]
    total: int
    limit: int
    offset: int
    has_more: bool


class TransactionCorrectionResponse(BaseModel):
    """Correction confirmation."""
    message: str
    transaction_id: str
    field_corrected: str
    old_value: Optional[str] = None
    new_value: str


class TransactionStats(BaseModel):
    """Transaction statistics."""
    total_transactions: int
    total_amount: str
    average_amount: str
    categories: Dict[str, Any]
    sources: Dict[str, Any]
