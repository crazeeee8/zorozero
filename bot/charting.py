import io
import pandas as pd
import mplfinance as mpf
import logging
from .config import settings

def generate_chart_image(df: pd.DataFrame, title: str) -> bytes:
    """
    Generates a PNG image of a price chart with MACD.
    
    Args:
        df: DataFrame containing OHLCV and MACD data.
        title: The chart title.
        
    Returns:
        The PNG image as a bytes object.
    """
    if df.empty:
        logging.warning("Attempted to generate chart from an empty DataFrame.")
        return b""

    try:
        # Ensure the index is a DatetimeIndex, required by mplfinance
        df.index.name = 'Date'

        # Define MACD plot
        macd_plot = mpf.make_addplot(df['macd'], panel=2, color='blue', title="MACD")
        signal_plot = mpf.make_addplot(df['macd_signal'], panel=2, color='orange')
        # Histogram plotted with a secondary_y axis to avoid scaling issues
        hist_plot = mpf.make_addplot(df['macd_histogram'], panel=2, type='bar', color='gray', alpha=0.5, secondary_y=True)

        # Create the plot style and figure
        style = mpf.make_mpf_style(base_mpf_style='yahoo', gridstyle='--')
        fig, _ = mpf.plot(
            df,
            type='candle',
            style=style,
            title=f"\n{title}",
            ylabel='Price',
            addplot=[macd_plot, signal_plot, hist_plot],
            panel_ratios=(3, 2), # Main panel is 3x taller than MACD panel
            figsize=(15, 8),
            returnfig=True # Return the figure object
        )
        
        # Add an arrow pointing to the last candle where the signal occurred
        last_row = df.iloc[-1]
        arrow_y_pos = last_row['high'] * 1.02 # A little above the high
        fig.axes[0].annotate(
            'Signal',
            xy=(df.index[-1], last_row['close']),
            xytext=(df.index[-20], arrow_y_pos),
            arrowprops=dict(facecolor='red', shrink=0.05, width=2, headwidth=8),
            fontsize=12,
            color='red',
            fontweight='bold'
        )
        
        # Save the figure to a bytes buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        
        return buf.read()

    except Exception as e:
        logging.error(f"Failed to generate chart image: {e}", exc_info=True)
        return b""