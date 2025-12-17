"""
Merchant Schemas - Search and response schemas.
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List


# ==================== REQUEST SCHEMAS ====================

class MerchantCreate(BaseModel):
    """Create a new merchant (admin only)."""
    canonical_name: str = Field(..., max_length=255, description="Standardized name")
    category: str = Field(..., max_length=100, description="Primary category")
    subcategory: Optional[str] = Field(default=None, max_length=100)
    aliases: Optional[List[str]] = Field(default=None, description="Alternative names")
    logo_url: Optional[str] = Field(default=None, max_length=500)


# ==================== RESPONSE SCHEMAS ====================

class MerchantResponse(BaseModel):
    """Single merchant response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    canonical_name: str
    category: str
    subcategory: Optional[str] = None
    logo_url: Optional[str] = None


class MerchantSearchResult(BaseModel):
    """Merchant search results."""
    data: List[MerchantResponse]
    total: int
    query: str
