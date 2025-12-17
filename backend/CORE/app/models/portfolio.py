"""
Portfolio Model - Investment portfolio holdings.
Database-agnostic: Works with PostgreSQL (production) and SQLite (testing).
"""
from sqlalchemy import Column, String, DateTime, Numeric, Index, ForeignKey, TypeDecorator
from sqlalchemy.orm import relationship
import uuid
import enum
from datetime import datetime
from app.database import Base


class GUIDType(TypeDecorator):
    """Platform-independent GUID type."""
    impl = String(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if isinstance(value, str) else value
        return value


class AssetType(str, enum.Enum):
    """Types of portfolio assets."""
    STOCK = "stock"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTO = "crypto"
    BOND = "bond"
    COMMODITY = "commodity"
    OTHER = "other"


class PortfolioHolding(Base):
    """
    User investment portfolio holdings.
    
    Tracks user's investments across different asset types
    with current and purchase values.
    """
    __tablename__ = "portfolio_holdings"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique holding identifier"
    )
    
    user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Owner user ID"
    )
    
    # Asset Information
    symbol = Column(
        String(20),
        nullable=False,
        comment="Asset symbol (e.g., AAPL, BTC)"
    )
    name = Column(
        String(255),
        nullable=True,
        comment="Full asset name"
    )
    asset_type = Column(
        String(20),
        default="stock",
        nullable=False,
        comment="Asset type: stock, etf, crypto, etc."
    )
    
    # Holdings
    quantity = Column(
        Numeric(18, 8),  # Supports fractional shares and crypto
        nullable=False,
        comment="Number of units held"
    )
    purchase_price = Column(
        Numeric(18, 8),
        nullable=False,
        comment="Average purchase price per unit"
    )
    current_price = Column(
        Numeric(18, 8),
        nullable=True,
        comment="Current market price per unit"
    )
    
    # Currency
    currency = Column(
        String(3),
        default="USD",
        nullable=False,
        comment="Currency code (USD, EUR, INR, etc.)"
    )
    
    # Timestamps
    purchase_date = Column(
        DateTime,
        nullable=True,
        comment="Date of purchase"
    )
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last price update timestamp"
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    __table_args__ = (
        Index("idx_portfolio_user", user_id),
        Index("idx_portfolio_symbol", symbol),
    )
    
    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, symbol={self.symbol}, qty={self.quantity})>"
    
    @property
    def current_value(self) -> float:
        """Calculate current value of holding."""
        if self.current_price and self.quantity:
            return float(self.current_price * self.quantity)
        return 0.0
    
    @property
    def gain_loss(self) -> float:
        """Calculate unrealized gain/loss."""
        if self.current_price and self.purchase_price and self.quantity:
            return float((self.current_price - self.purchase_price) * self.quantity)
        return 0.0
