import os
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    """Loads all settings from environment variables."""
    # API Keys & Webhooks
    DISCORD_WEBHOOK: str = os.environ.get("DISCORD_WEBHOOK", "").strip()
    CRYPTOPANIC_API_KEY: str = os.environ.get("CRYPTOPANIC_API_KEY", "").strip()

    # Market Settings
    SYMBOL: str = os.environ.get("SYMBOL", "BTC-USD").strip()
    TIMEFRAME_15M: str = "15m"
    TIMEFRAME_1D: str = "1d"

    # MACD Parameters
    MACD_FAST: int = int(os.environ.get("MACD_FAST", "8"))
    MACD_SLOW: int = int(os.environ.get("MACD_SLOW", "15"))
    MACD_SIGNAL: int = int(os.environ.get("MACD_SIGNAL", "9"))

    # Bot Behavior
    POLL_SECONDS: int = int(os.environ.get("POLL_SECONDS", "60"))
    LOOKBACK_PERIOD_15M: str = "5d" # How much 15m data to fetch
    LOOKBACK_PERIOD_1D: str = "1y" # How much 1d data to fetch

    # System
    PORT: int = int(os.environ.get("PORT", "10000"))


settings = Settings()