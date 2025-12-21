from GoogleNews import GoogleNews
from transformers import pipeline
from app.schemas.analysis import NewsItem, SentimentType
import logging

# Setup Logging
logger = logging.getLogger(__name__)

class NewsEngine:
    def __init__(self):
        # Initialize Google News (India, English)
        self.googlenews = GoogleNews(lang='en', region='IN')
        
        # Initialize FinBERT (The Financial Brain)
        # NOTE: This will download ~400MB the first time you run it.
        try:
            self.classifier = pipeline("sentiment-analysis", model="ProsusAI/finbert")
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {e}")
            self.classifier = None

    def _get_search_query(self, symbol: str, asset_name: str, asset_type: str) -> str:
        """
        Determines the best search query based on Asset Type.
        """
        if asset_type == "gold":
            return "Gold Price India"
        elif asset_type == "mutual_fund":
            # Search for the Fund House or Category
            # e.g., "SBI Mutual Fund" or "Small Cap Mutual Fund"
            return f"{asset_name} Mutual Fund" 
        else: # Stock
            # Clean up symbol if needed, but Name is better for news
            return f"{asset_name} share news"

    def fetch_and_analyze(self, symbol: str, asset_name: str, asset_type: str) -> list[NewsItem]:
        """
        Main function: Fetches news -> Runs AI -> Returns Structured Data
        """
        query = self._get_search_query(symbol, asset_name, asset_type)
        logger.info(f"Searching news for: {query}")
        
        # 1. Fetch News
        self.googlenews.clear() # Clear past results
        self.googlenews.search(query)
        results = self.googlenews.result()[:5] # Top 5 headlines only
        
        if not results:
            logger.warning(f"No news found for {query}")
            return []

        analyzed_news = []
        
        # 2. Analyze Sentiment
        for item in results:
            title = item['title']
            link = item['link'] # Useful if you want to show 'Read More' link
            
            sentiment_result = "neutral"
            score = 0.0
            
            if self.classifier:
                try:
                    # FinBERT returns [{'label': 'positive', 'score': 0.9}]
                    prediction = self.classifier(title)[0]
                    sentiment_result = prediction['label']
                    score = prediction['score']
                except Exception as e:
                    logger.error(f"Error analyzing headline '{title}': {e}")
            
            # Map FinBERT label to our Enum
            sentiment_enum = SentimentType.NEUTRAL
            if sentiment_result == 'positive':
                sentiment_enum = SentimentType.POSITIVE
            elif sentiment_result == 'negative':
                sentiment_enum = SentimentType.NEGATIVE
                
            analyzed_news.append(NewsItem(
                title=title,
                source=item.get('media', 'Google News'),
                sentiment=sentiment_enum,
                score=round(score, 2)
            ))
            
        return analyzed_news
    