import yfinance as yf
import requests
import pandas as pd
import numpy as np
from prophet import Prophet
from datetime import date, timedelta
from app.schemas.analysis import PredictionPoint, MetricCard
import logging

logger = logging.getLogger(__name__)

class PredictionEngine:
    def _fetch_history(self, symbol: str, asset_type: str) -> pd.DataFrame:
        """
        Fetches last 2 years of data and returns a clean DataFrame [ds, y]
        """
        try:
            if asset_type == "mutual_fund":
                # MFAPI.in logic
                url = f"https://api.mfapi.in/mf/{symbol}"
                data = requests.get(url).json()['data']
                # Convert to DataFrame
                df = pd.DataFrame(data)
                df = df.rename(columns={'date': 'ds', 'nav': 'y'})
                df['ds'] = pd.to_datetime(df['ds'], format='%d-%m-%Y')
                df['y'] = pd.to_numeric(df['y'])
                # Slice last 2 years
                cutoff = pd.to_datetime('today') - pd.Timedelta(days=730)
                df = df[df['ds'] > cutoff]
                return df.sort_values(by='ds')
            
            else:
                # Yahoo Finance Logic (Stocks & Gold)
                ticker = yf.Ticker(symbol)
                # '2y' period is optimal for daily seasonality
                hist = ticker.history(period="2y")
                df = hist.reset_index()[['Date', 'Close']]
                df = df.rename(columns={'Date': 'ds', 'Close': 'y'})
                df['ds'] = pd.to_datetime(df['ds']).dt.tz_localize(None) # Remove timezone
                return df
                
        except Exception as e:
            logger.error(f"Data fetch error for {symbol}: {e}")
            return pd.DataFrame()

    def run_forecast(self, symbol: str, asset_type: str) -> tuple[list[PredictionPoint], MetricCard]:
        """
        Main function: Returns Graph Data + Metrics
        """
        # 1. Get Data
        df = self._fetch_history(symbol, asset_type)
        
        if df.empty or len(df) < 30:
            raise ValueError("Not enough historical data to predict")

        # 2. Train Prophet (The AI)
        # daily_seasonality=True helps with stock market patterns
        model = Prophet(daily_seasonality=True, yearly_seasonality=True)
        model.fit(df)
        
        # 3. Predict Future (30 Days)
        future = model.make_future_dataframe(periods=30)
        forecast = model.predict(future)
        
        # 4. Calculate Volatility (Risk)
        # Std Dev of last 30 days returns
        recent_data = df.tail(30).copy()
        recent_data['pct_change'] = recent_data['y'].pct_change()
        volatility = recent_data['pct_change'].std() * 100 # Percentage
        
        # Risk Score Logic (0-10)
        # Normal volatility is ~1-2%. Crypto is 5%+. Gold is 0.5%.
        risk_score = min(volatility * 2, 10) 

        # 5. Package Data for Frontend
        current_price = df.iloc[-1]['y']
        future_price = forecast.iloc[-1]['yhat']
        growth_pct = ((future_price - current_price) / current_price) * 100
        
        # Build Points List
        points = []
        
        # Add History (Last 30 days only to keep graph clean)
        history_slice = df.tail(30)
        for _, row in history_slice.iterrows():
            points.append(PredictionPoint(
                date=row['ds'].strftime("%Y-%m-%d"),
                price=round(row['y'], 2),
                type="history"
            ))
            
        # Add Prediction (Next 30 days)
        future_slice = forecast.tail(30)
        for _, row in future_slice.iterrows():
            points.append(PredictionPoint(
                date=row['ds'].strftime("%Y-%m-%d"),
                price=round(row['yhat'], 2),
                type="forecast",
                confidence_lower=round(row['yhat_lower'], 2),
                confidence_upper=round(row['yhat_upper'], 2)
            ))
            
        metrics = MetricCard(
            current_price=round(current_price, 2),
            predicted_price_30d=round(future_price, 2),
            growth_percentage=round(growth_pct, 2),
            risk_score=round(risk_score, 1)
        )
        
        return points, metrics