import pandas as pd
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def calculate_rsi(prices, period=14):
    """
    Calculate the Relative Strength Index (RSI) for the given prices.

    Args:
    prices: list: List of price data.
    period: int: The period for RSI calculation, default is 14.

    Returns:
    float: The most recent RSI value, or None if not enough data.
    """
    # Log the entire price series being used for calculation
    logging.info(f"Calculating RSI for the full price list: {prices}")
    
    # Ensure there is enough data to calculate RSI
    if len(prices) < period:
        logging.warning(f"Not enough data to calculate RSI. Required: {period}, provided: {len(prices)}")
        return None

    # Calculate the differences between consecutive prices
    delta = pd.Series(prices).diff()
    logging.info(f"Price differences (delta): {delta.tolist()}")

    # Separate gains and losses
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    logging.info(f"Gains: {gain.tolist()}, Losses: {loss.tolist()}")

    # Calculate the rolling average of gains and losses
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    logging.info(f"Average gain: {avg_gain.tolist()}, Average loss: {avg_loss.tolist()}")

    # Handle case when avg_loss is zero to avoid division by zero
    if avg_loss.iloc[-1] == 0:
        logging.warning("Average loss is zero, cannot calculate RSI. Returning RSI as 100.")
        return 100  # If there's no loss, RSI is set to 100 (max value).

    # Calculate the Relative Strength (RS) and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    logging.info(f"RSI series: {rsi.tolist()}")

    # Return the most recent RSI value
    latest_rsi = rsi.iloc[-1] if not rsi.empty else None
    logging.info(f"Most recent RSI value: {latest_rsi}")
    
    return latest_rsi
