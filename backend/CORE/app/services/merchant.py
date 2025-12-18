"""
Merchant Service - Enhanced with multi-tier fuzzy search.
Supports exact match, alias search, and fuzzy pattern matching.
"""
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, List, Tuple
from uuid import UUID
import json

from app.models.merchant import MerchantMaster
from app.utils.exceptions import NotFoundException


class MerchantService:
    """
    Merchant service with multi-tier search.
    
    Search tiers:
    1. Exact match on canonical_name
    2. Alias match (stored in JSON)
    3. Fuzzy pattern match (LIKE with variations)
    """
    
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
        """Create a new merchant."""
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
        """Get merchant by ID."""
        merchant = self.db.query(MerchantMaster).filter(
            MerchantMaster.id == merchant_id
        ).first()
        
        if not merchant:
            raise NotFoundException(detail="Merchant not found")
        
        return merchant
    
    def search(self, query: str, limit: int = 20) -> Tuple[List[MerchantMaster], int]:
        """
        Multi-tier fuzzy search for merchants.
        
        Tier 1: Exact match (score 1.0)
        Tier 2: Starts with query (score 0.9)
        Tier 3: Contains query (score 0.8)
        Tier 4: Alias match (score 0.7)
        
        Returns (merchants, total_count) sorted by relevance.
        """
        if not query or len(query) < 2:
            return [], 0
        
        query_lower = query.lower().strip()
        results = {}  # id -> (score, merchant)
        
        # Tier 1: Exact match
        exact = self.db.query(MerchantMaster).filter(
            func.lower(MerchantMaster.canonical_name) == query_lower
        ).all()
        for m in exact:
            results[str(m.id)] = (1.0, m)
        
        # Tier 2: Starts with
        starts = self.db.query(MerchantMaster).filter(
            func.lower(MerchantMaster.canonical_name).startswith(query_lower)
        ).limit(limit).all()
        for m in starts:
            if str(m.id) not in results:
                results[str(m.id)] = (0.9, m)
        
        # Tier 3: Contains
        contains_pattern = f"%{query_lower}%"
        contains = self.db.query(MerchantMaster).filter(
            MerchantMaster.canonical_name.ilike(contains_pattern)
        ).limit(limit).all()
        for m in contains:
            if str(m.id) not in results:
                results[str(m.id)] = (0.8, m)
        
        # Tier 4: Alias search
        # Search in JSON aliases field
        all_merchants = self.db.query(MerchantMaster).filter(
            MerchantMaster.aliases.isnot(None)
        ).all()
        for m in all_merchants:
            if str(m.id) in results:
                continue
            try:
                aliases = json.loads(m.aliases) if m.aliases else []
                for alias in aliases:
                    if query_lower in alias.lower():
                        results[str(m.id)] = (0.7, m)
                        break
            except json.JSONDecodeError:
                pass
        
        # Sort by score descending, then by name
        sorted_results = sorted(
            results.values(),
            key=lambda x: (-x[0], x[1].canonical_name)
        )
        
        # Apply limit
        merchants = [m for _, m in sorted_results[:limit]]
        total = len(sorted_results)
        
        return merchants, total
    
    def get_by_category(self, category: str) -> List[MerchantMaster]:
        """Get all merchants in a category."""
        return self.db.query(MerchantMaster).filter(
            MerchantMaster.category == category
        ).order_by(MerchantMaster.canonical_name).all()
    
    def match_raw_text(self, raw_text: str) -> Optional[MerchantMaster]:
        """
        Match raw merchant text to a known merchant.
        
        For Person 2 ML integration - called during transaction processing.
        Example: "STARBUCKS #12345 EAST SIDE" -> "Starbucks"
        """
        if not raw_text:
            return None
        
        # Normalize
        text_lower = raw_text.lower().strip()
        
        # Try exact
        merchants, _ = self.search(text_lower, limit=5)
        if merchants:
            return merchants[0]
        
        # Try first word (often the merchant name)
        first_word = text_lower.split()[0] if text_lower.split() else ""
        if len(first_word) >= 3:
            merchants, _ = self.search(first_word, limit=5)
            if merchants:
                return merchants[0]
        
        return None
