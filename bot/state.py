from dataclasses import dataclass, field
from typing import Dict, Optional, Set
import aiohttp

@dataclass
class BotState:
    """Holds the runtime state of the bot."""
    # Tracks state for "early warning" on the unclosed 15m candle
    last_15m_macd_early_state: Optional[str] = None
    
    # Tracks state for "confirmation" on the closed 15m candle
    last_15m_signal_confirm_state: Optional[str] = None
    
    # Tracks state for the daily chart
    last_1d_macd_state: Optional[str] = None
    
    # Stores IDs of news/events already sent to avoid duplicates
    seen_news_ids: Set[str] = field(default_factory=set)
    seen_event_ids: Set[str] = field(default_factory=set)
    
    # Shared HTTP session for performance
    session: Optional[aiohttp.ClientSession] = None
    
    # Tracks last time daily updates were run
    last_daily_update_date: Optional[str] = None

# Global state instance
STATE = BotState()