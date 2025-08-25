import pandas as pd
import pandas_ta as ta
import logging
from typing import List, Tuple
from .config import settings
from .state import STATE

def calculate_macd(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates MACD indicators and appends them to the DataFrame."""
    if df.empty or 'close' not in df.columns:
        return df

    try:
        # Use the MACD parameters from the config
        macd = ta.macd(
            df["close"],
            fast=settings.MACD_FAST,
            slow=settings.MACD_SLOW,
            signal=settings.MACD_SIGNAL
        )
        if macd is None or macd.empty:
            raise ValueError("pandas_ta.macd returned None or empty DataFrame.")
            
        # Standardize column names based on parameters
        base_name = f"MACD_{settings.MACD_FAST}_{settings.MACD_SLOW}_{settings.MACD_SIGNAL}"
        macd.columns = ['macd', 'macd_histogram', 'macd_signal']
        
        return pd.concat([df, macd], axis=1)
    except Exception as e:
        logging.error(f"Error calculating MACD: {e}")
        return df

def _check_cross(
    series: pd.Series,
    prev_state: str,
    lookback_idx_curr: int = -1, # -1 is the current, unclosed candle
    lookback_idx_prev: int = -2  # -2 is the last closed candle
) -> Tuple[bool, str]:
    """Generic function to check for a zero-line cross."""
    if len(series) < abs(lookback_idx_prev):
        return False, prev_state
    
    prev_val = series.iloc[lookback_idx_prev]
    curr_val = series.iloc[lookback_idx_curr]
    
    new_state = "above_zero" if curr_val > 0 else "below_zero"
    
    crossed_up = prev_val <= 0 and curr_val > 0
    crossed_down = prev_val >= 0 and curr_val < 0
    
    did_cross = (crossed_up or crossed_down) and new_state != prev_state
    
    return did_cross, new_state

def find_signals(df_15m: pd.DataFrame, df_1d: pd.DataFrame) -> List[dict]:
    """Analyzes dataframes for all required MACD signals."""
    signals = []
    
    # --- 15-Minute Timeframe Analysis ---
    if not df_15m.empty and all(c in df_15m.columns for c in ['macd', 'macd_signal']):
        # 1. EARLY WARNING: MACD line cross (intra-candle)
        # Compares the current unclosed candle (-1) with the last closed one (-2)
        macd_crossed, new_state = _check_cross(df_15m['macd'], STATE.last_15m_macd_early_state)
        if macd_crossed:
            direction = "ABOVE" if new_state == 'above_zero' else "BELOW"
            signals.append({
                "title": f"{settings.SYMBOL} 15m (Early Warning): MACD Line Crossing {direction} Zero",
                "description": "The MACD line is crossing the zero level on the current, unclosed 15-minute candle.",
                "dataframe": df_15m.tail(100)
            })
            STATE.last_15m_macd_early_state = new_state
        # Reset early warning state if the candle closes without a signal, allowing re-trigger
        elif len(df_15m) > 2 and STATE.last_15m_macd_early_state is not None:
             STATE.last_15m_macd_early_state = None


        # 2. CONFIRMATION: Signal line cross (after candle close)
        # Compares the last closed candle (-2) with the one before it (-3)
        signal_crossed, new_state = _check_cross(df_15m['macd_signal'], STATE.last_15m_signal_confirm_state, -2, -3)
        if signal_crossed:
            direction = "ABOVE" if new_state == 'above_zero' else "BELOW"
            signals.append({
                "title": f"{settings.SYMBOL} 15m (Confirmation): Signal Line Crossed {direction} Zero",
                "description": "The Signal line crossed the zero level on the recently closed 15-minute candle.",
                "dataframe": df_15m.tail(100)
            })
            STATE.last_15m_signal_confirm_state = new_state

    # --- 1-Day Timeframe Analysis ---
    if not df_1d.empty and 'macd' in df_1d.columns:
        # 3. MACD Line cross on closed daily candle
        macd_crossed_1d, new_state_1d = _check_cross(df_1d['macd'], STATE.last_1d_macd_state, -2, -3)
        if macd_crossed_1d:
            direction = "ABOVE" if new_state_1d == 'above_zero' else "BELOW"
            signals.append({
                "title": f"{settings.SYMBOL} 1D: MACD Line Crossed {direction} Zero",
                "description": "The MACD line crossed the zero level on the daily chart.",
                "dataframe": df_1d.tail(200)
            })
            STATE.last_1d_macd_state = new_state_1d
            
    return signals