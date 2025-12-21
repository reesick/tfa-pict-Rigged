from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.services.news_engine import NewsEngine
from app.services.prediction_engine import PredictionEngine
from app.schemas.analysis import AssetAnalysisResponse, AssetType, VerdictType, SentimentType
import logging
import asyncio

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize Services
# In production, use dependency injection (Depends) for these
news_engine = NewsEngine()
prediction_engine = PredictionEngine()

def calculate_verdict(growth_pct: float, sentiment_score: float) -> tuple[VerdictType, str]:
    """
    The Brain: Combines Math (Growth) + Vibe (Sentiment) to decide.
    Sentiment Score is calculated as: (Positive - Negative) / Total
    Range: -1.0 (All Bad) to +1.0 (All Good)
    """
    
    # Logic Table
    if growth_pct > 2.0: # Math says UP
        if sentiment_score > 0.2:
            return VerdictType.STRONG_BUY, "Price trend is strong and news is positive."
        elif sentiment_score < -0.2:
            return VerdictType.HOLD, "Math says UP, but bad news suggests a trap. Wait."
        else:
            return VerdictType.BUY, "Technical trend is up, neutral news."
            
    elif growth_pct < -2.0: # Math says DOWN
        if sentiment_score > 0.5:
            return VerdictType.BUY, "Price is falling but news is very positive. Value buy opportunity."
        elif sentiment_score < -0.2:
            return VerdictType.STRONG_SELL, "Falling price and bad news. Get out."
        else:
            return VerdictType.SELL, "Downward trend with no positive catalyst."
            
    else: # Flat / Noise (-2% to +2%)
        return VerdictType.HOLD, "Market is sideways. No clear signal."

@router.get("/analyze/{asset_type}/{symbol}", response_model=AssetAnalysisResponse)
async def analyze_asset(asset_type: AssetType, symbol: str, asset_name: str):
    """
    Main Endpoint: 
    1. Fetches Price History & Runs Prophet (Math)
    2. Fetches Google News & Runs FinBERT (Sentiment)
    3. Combines them into a Verdict
    """
    try:
        # Run Math and News in parallel (Async) to save time
        # Note: PredictionEngine is CPU bound, so we run it in a threadpool
        loop = asyncio.get_event_loop()
        
        # 1. Start Math Engine
        future_math = loop.run_in_executor(None, prediction_engine.run_forecast, symbol, asset_type.value)
        
        # 2. Start News Engine
        future_news = loop.run_in_executor(None, news_engine.fetch_and_analyze, symbol, asset_name, asset_type.value)
        
        # 3. Wait for both
        (points, metrics), news_items = await asyncio.gather(future_math, future_news)
        
        # 4. Calculate Aggregate Sentiment Score
        # Simple algorithm: Positive (+1), Negative (-1), Neutral (0)
        sentiment_total = 0
        for item in news_items:
            if item.sentiment == SentimentType.POSITIVE:
                sentiment_total += 1
            elif item.sentiment == SentimentType.NEGATIVE:
                sentiment_total -= 1
        
        # Normalize score (-1 to 1)
        normalized_sentiment = 0
        if news_items:
            normalized_sentiment = sentiment_total / len(news_items)

        # 5. Generate Verdict
        verdict, reason = calculate_verdict(metrics.growth_percentage, normalized_sentiment)

        return AssetAnalysisResponse(
            symbol=symbol,
            asset_name=asset_name,
            verdict=verdict,
            verdict_reason=reason,
            graph_data=points,
            news_feed=news_items,
            metrics=metrics
        )

    except ValueError as e:
        # Expected error (e.g., "Not enough data")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Internal AI Error")
    