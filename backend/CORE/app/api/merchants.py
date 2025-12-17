"""
Merchant API Endpoints - Search and lookup.
"""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.merchant import (
    MerchantCreate,
    MerchantResponse,
    MerchantSearchResult
)
from app.services.merchant import MerchantService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/merchants", tags=["Merchants"])


# ==================== HELPER ====================
def to_response(m) -> MerchantResponse:
    """Convert MerchantMaster model to response."""
    return MerchantResponse(
        id=str(m.id),
        canonical_name=m.canonical_name,
        category=m.category,
        subcategory=m.subcategory,
        logo_url=m.logo_url
    )


# ==================== SEARCH ====================
@router.get("/search", response_model=MerchantSearchResult, summary="Search merchants")
def search_merchants(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search merchants by name."""
    service = MerchantService(db)
    merchants, total = service.search(q, limit=limit)
    
    return MerchantSearchResult(
        data=[to_response(m) for m in merchants],
        total=total,
        query=q
    )


# ==================== GET ONE ====================
@router.get("/{merchant_id}", response_model=MerchantResponse, summary="Get merchant")
def get_merchant(
    merchant_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get merchant by ID."""
    service = MerchantService(db)
    merchant = service.get_by_id(merchant_id)
    return to_response(merchant)


# ==================== CREATE (ADMIN) ====================
@router.post("/", response_model=MerchantResponse, status_code=status.HTTP_201_CREATED, summary="Create merchant")
def create_merchant(
    data: MerchantCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new merchant. (Admin only - TODO: add admin check)"""
    service = MerchantService(db)
    merchant = service.create(
        canonical_name=data.canonical_name,
        category=data.category,
        subcategory=data.subcategory,
        aliases=data.aliases,
        logo_url=data.logo_url
    )
    return to_response(merchant)
