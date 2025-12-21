from pydantic import BaseModel
from typing import List, Optional
from enum import Enum
from datetime import date

# 1. Enums to keep things consistent
class AssetType(str, Enum):
    STOCK = "stock"
    MUTUAL_FUND = "mutual_fund"
    GOLD = "gold"

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"

class VerdictType(str, Enum):
    STRONG_BUY = "Strong Buy"
    BUY = "Buy"
    HOLD = "Hold"
    SELL = "Sell"
    STRONG_SELL = "Strong Sell"

# 2. Components of the Dashboard

class NewsItem(BaseModel):
    title: str
    source: str = "Google News"
    sentiment: SentimentType
    score: float  # How confident is FinBERT? (0.0 to 1.0)

class PredictionPoint(BaseModel):
    date: str  # Format: "YYYY-MM-DD"
    price: float
    type: str  # "history" or "forecast"
    confidence_lower: Optional[float] = None # For the "Cloud" visual
    confidence_upper: Optional[float] = None

class MetricCard(BaseModel):
    current_price: float
    predicted_price_30d: float
    growth_percentage: float
    risk_score: float # 0 to 10 (calculated from Volatility + Sentiment)

# 3. The Master Response (What React receives)
class AssetAnalysisResponse(BaseModel):
    symbol: str
    asset_name: str
    verdict: VerdictType
    verdict_reason: str  # "Math says UP, but News is Negative"
    
    # Part A: The Visuals
    graph_data: List[PredictionPoint]
    
    # Part B: The Context
    news_feed: List[NewsItem]
    
    # Part C: The Simulator Data
    metrics: MetricCard
    
    class Config:
        from_attributes = True
        