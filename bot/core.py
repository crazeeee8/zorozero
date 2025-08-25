import asyncio
import logging
from datetime import datetime
from .config import settings
from .state import STATE
from .data import fetch_ohlcv
from .analysis import calculate_macd, find_signals
from .charting import generate_chart_image
from .services.discord import send_message, send_file
from .services.news import get_daily_news
from .services.events import get_upcoming_events

async def startup_message():
    """Sends a startup message to Discord."""
    logging.info("Sending startup message.")
    await send_message(
        f"✅ **ZeroZoro Bot Started**\n"
        f"Monitoring `{settings.SYMBOL}` with MACD(`{settings.MACD_FAST}`,`{settings.MACD_SLOW}`,`{settings.MACD_SIGNAL}`)\n"
        f"Polling every {settings.POLL_SECONDS / 60:.0f} minutes."
    )

async def check_market_signals():
    """Fetches market data, analyzes for signals, and sends alerts."""
    # Fetch data for both timeframes concurrently
    data_15m_task = fetch_ohlcv(settings.SYMBOL, settings.TIMEFRAME_15M, settings.LOOKBACK_PERIOD_15M)
    data_1d_task = fetch_ohlcv(settings.SYMBOL, settings.TIMEFRAME_1D, settings.LOOKBACK_PERIOD_1D)
    df_15m, df_1d = await asyncio.gather(data_15m_task, data_1d_task)

    # Calculate MACD for both
    df_15m_macd = calculate_macd(df_15m)
    df_1d_macd = calculate_macd(df_1d)

    # Find signals
    signals = find_signals(df_15m_macd, df_1d_macd)
    
    for signal in signals:
        logging.info(f"Signal found: {signal['title']}")
        
        # Generate chart
        chart_bytes = generate_chart_image(signal['dataframe'], signal['title'])
        
        # Send alert with chart
        content = f"**🚨 ALERT: {signal['title']}**\n{signal['description']}"
        if chart_bytes:
            await send_file(
                content=content,
                file_bytes=chart_bytes,
                filename=f"{settings.SYMBOL}_alert.png"
            )
        else: # Fallback to text if chart fails
            await send_message(content)

async def check_daily_updates():
    """Checks for and sends daily news and events."""
    today = datetime.utcnow().strftime('%Y-%m-%d')
    if STATE.last_daily_update_date != today:
        logging.info("Performing daily news and events check...")
        
        # Get news from CryptoPanic
        news_messages = await get_daily_news()
        for msg in news_messages:
            await send_message(msg)
            await asyncio.sleep(1)
            
        # Get events from CoinMarketCal
        event_messages = await get_upcoming_events()
        for msg in event_messages:
            await send_message(msg)
            await asyncio.sleep(1)

        STATE.last_daily_update_date = today

async def monitor():
    """The main monitoring loop of the bot."""
    await startup_message()
    
    while True:
        try:
            await check_market_signals()
            await check_daily_updates()
            
        except Exception as e:
            logging.error(f"An unexpected error occurred in the monitor loop: {e}", exc_info=True)
            await send_message(f"🔥 **ERROR:** An unexpected error occurred: `{e}`. The bot is still running but may need attention.")
            
        await asyncio.sleep(settings.POLL_SECONDS)