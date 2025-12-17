"""
Merchant Service - Simple business logic for merchant lookup.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional, List, Tuple
from uuid import UUID
import json

from app.models.merchant import MerchantMaster
from app.utils.exceptions import NotFoundException


class MerchantService:
    """Simple merchant service for search and lookup."""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== CREATE ====================
    def create(
        self,
        canonical_name: str,
        category: str,
        subcategory: Optional[str] = None,
        aliases: Optional[List[str]] = None,
        logo_url: Optional[str] = None
    ) -> MerchantMaster:
        """Create a new merchant (admin only)."""
        merchant = MerchantMaster(
            canonical_name=canonical_name,
            category=category,
            subcategory=subcategory,
            aliases=json.dumps(aliases) if aliases else None,
            logo_url=logo_url
        )
        self.db.add(merchant)
        self.db.commit()
        self.db.refresh(merchant)
        return merchant
    
    # ==================== READ ====================
    def get_by_id(self, merchant_id: UUID) -> MerchantMaster:
        """Get merchant by ID. Raises NotFoundException if not found."""
        merchant = self.db.query(MerchantMaster).filter(
            MerchantMaster.id == merchant_id
        ).first()
        
        if not merchant:
            raise NotFoundException(detail="Merchant not found")
        
        return merchant
    
    def search(self, query: str, limit: int = 20) -> Tuple[List[MerchantMaster], int]:
        """Search merchants by name. Returns (merchants, total_count)."""
        if not query or len(query) < 2:
            return [], 0
        
        # Case-insensitive search on canonical_name
        search_pattern = f"%{query.lower()}%"
        
        db_query = self.db.query(MerchantMaster).filter(
            MerchantMaster.canonical_name.ilike(search_pattern)
        )
        
        total = db_query.count()
        merchants = db_query.order_by(MerchantMaster.canonical_name).limit(limit).all()
        
        return merchants, total
    
    def get_by_category(self, category: str) -> List[MerchantMaster]:
        """Get all merchants in a category."""
        return self.db.query(MerchantMaster).filter(
            MerchantMaster.category == category
        ).order_by(MerchantMaster.canonical_name).all()
