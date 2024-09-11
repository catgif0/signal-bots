import pandas as pd

def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for the given prices.

    Args:
    prices: list: List of price data.
    period: int: The period for RSI calculation, default is 14.

    Returns:
    float: The most recent RSI value.
    """
    if len(prices) < period:
        return None  # Not enough data to calculate RSI
    
    delta = pd.Series(prices).diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return rsi.iloc[-1]  # Return the most recent RSI value
