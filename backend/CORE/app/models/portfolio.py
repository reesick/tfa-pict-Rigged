"""Portfolio model - Investment holdings tracking."""
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base
import enum


class AssetType(str, enum.Enum):
    """Types of investment assets."""
    STOCK = "stock"
    CRYPTO = "crypto"
    BOND = "bond"
    MUTUAL_FUND = "mutual_fund"
    ETF = "etf"
    COMMODITY = "commodity"


class PortfolioHolding(Base):
    """
    Investment portfolio holdings model.
    
    Tracks user's traditional and crypto investments.
    Person 3 updates crypto holdings from blockchain data.
    """
    __tablename__ = "portfolio_holdings"
    
    # Primary Key
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique holding identifier"
    )
    
    # Foreign Key
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Portfolio owner"
    )
    
    # Asset Information
    asset_type = Column(
        Enum(AssetType),
        nullable=False,
        index=True,
        comment="Type of asset: stock, crypto, bond, etc."
    )
    identifier = Column(
        String(100),
        nullable=False,
        comment="Asset identifier: ticker symbol (AAPL) or contract address (0x...)"
    )
    name = Column(
        String(255),
        nullable=True,
        comment="Asset name: Apple Inc., Bitcoin, etc."
    )
    
    # Holdings Data
    units = Column(
        Numeric(20, 8),
        nullable=False,
        comment="Number of units held (8 decimals for crypto precision)"
    )
    cost_basis = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Average purchase price per unit"
    )
    
    # Valuation (updated by background jobs or Person 3)
    current_price = Column(
        Numeric(12, 2),
        nullable=True,
        comment="Current market price per unit"
    )
    last_valuation = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Total current value (units * current_price)"
    )
    valuation_currency = Column(
        String(3),
        default="USD",
        nullable=False,
        comment="ISO 4217 currency code for valuation"
    )
    
    # Blockchain Data (for crypto assets - Person 3)
    chain = Column(
        String(50),
        nullable=True,
        comment="Blockchain network: ethereum, polygon, bitcoin, etc."
    )
    wallet_address = Column(
        String(100),
        nullable=True,
        comment="Wallet address holding this asset"
    )
    
    # Timestamps
    acquired_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When asset was acquired"
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last update timestamp"
    )
    
    # Relationships
    user = relationship(
        "User",
        back_populates="portfolios",
        doc="Portfolio owner"
    )
    
    # Indexes
    __table_args__ = (
        Index('idx_portfolio_user', 'user_id'),
        Index('idx_portfolio_asset_type', 'asset_type'),
        Index('idx_portfolio_identifier', 'identifier'),
        Index('idx_portfolio_chain', 'chain'),
    )
    
    def __repr__(self):
        return f"<PortfolioHolding(id={self.id}, type={self.asset_type}, identifier={self.identifier}, units={self.units})>"
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "asset_type": self.asset_type.value if self.asset_type else None,
            "identifier": self.identifier,
            "name": self.name,
            "units": float(self.units) if self.units else None,
            "cost_basis": float(self.cost_basis) if self.cost_basis else None,
            "current_price": float(self.current_price) if self.current_price else None,
            "last_valuation": float(self.last_valuation) if self.last_valuation else None,
            "valuation_currency": self.valuation_currency,
            "chain": self.chain,
            "wallet_address": self.wallet_address,
            "acquired_at": self.acquired_at.isoformat() if self.acquired_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }
    
    def calculate_profit_loss(self) -> dict:
        """
        Calculate profit/loss for this holding.
        
        Returns:
            Dictionary with profit/loss metrics
        """
        if not self.cost_basis or not self.current_price or not self.units:
            return {
                "total_cost": None,
                "current_value": None,
                "profit_loss": None,
                "profit_loss_percentage": None
            }
        
        total_cost = float(self.cost_basis * self.units)
        current_value = float(self.current_price * self.units)
        profit_loss = current_value - total_cost
        profit_loss_pct = (profit_loss / total_cost * 100) if total_cost != 0 else 0
        
        return {
            "total_cost": round(total_cost, 2),
            "current_value": round(current_value, 2),
            "profit_loss": round(profit_loss, 2),
            "profit_loss_percentage": round(profit_loss_pct, 2)
        }
