import asyncio
import logging
import pandas as pd
import yfinance as yf
from .config import settings

async def fetch_ohlcv(symbol: str, timeframe: str, period: str) -> pd.DataFrame:
    """
    Fetches OHLCV data from Yahoo Finance asynchronously.
    
    Args:
        symbol: The market symbol (e.g., 'BTC-USD').
        timeframe: The candle interval (e.g., '15m', '1d').
        period: The duration to fetch data for (e.g., '5d', '1y').
    
    Returns:
        A pandas DataFrame with OHLCV data.
    """
    try:
        # yfinance is synchronous, so we run it in a thread to avoid blocking asyncio
        df = await asyncio.to_thread(
            yf.download,
            tickers=symbol,
            period=period,
            interval=timeframe,
            progress=False
        )

        if df.empty:
            raise ValueError(f"No data returned from Yahoo Finance for {symbol} on {timeframe}.")

        # Basic validation
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Yahoo Finance data is missing required columns. Got: {df.columns}")
            
        df.rename(columns={col: col.lower() for col in required_cols}, inplace=True)

        return df
        
    except Exception as e:
        logging.error(f"Failed to fetch data from Yahoo Finance for {symbol} ({timeframe}): {e}")
        # Return an empty DataFrame on failure to prevent crashing the main loop
        return pd.DataFrame()