import logging
from collections import deque
from services.rsi_calculation import calculate_rsi  # Import RSI calculation function
from services.signal_generation import calculate_take_profit, calculate_stop_loss
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# High volume threshold for new lows signal
HIGH_VOLUME_THRESHOLD = 1.5  # 1.5x of the average volume
PRICE_DIFF_THRESHOLD = 0.2 / 100  # 0.2% price difference threshold
recent_lows = {}  # Track up to 3 recent lows with volume and RSI for each symbol

def format_volume(volume):
    """Formats volume to abbreviate large numbers like 1k, 1M."""
    if volume >= 1_000_000:
        return f"{volume / 1_000_000:.1f}M"
    elif volume >= 1_000:
        return f"{volume / 1_000:.1f}k"
    else:
        return f"{volume}"

def calculate_reward_risk(entry_price, stop_loss, reward_ratio=2):
    """
    Calculates the stop loss and take profits based on a reward-to-risk ratio.

    Args:
    entry_price (float): Entry price for the signal.
    stop_loss (float): The stop loss price.
    reward_ratio (float): The reward-to-risk ratio. Defaults to 2.

    Returns:
    tuple: (stop_loss, tp1, tp2, tp3) where each is a float.
    """
    risk = entry_price - stop_loss
    tp1 = entry_price + risk * reward_ratio
    tp2 = entry_price + risk * (reward_ratio * 2)
    tp3 = entry_price + risk * (reward_ratio * 3)
    return stop_loss, tp1, tp2, tp3

# New signal generation logic based on three lows and decreasing volume trend or RSI condition
def generate_new_signal(pair, current_price, price_data, volume_data, current_time):
    """
    Signal generation logic based on:
    1. Three new lows with decreasing volume trend or RSI conditions.
    
    Args:
    pair (str): The pair being analyzed (e.g., BTCUSDT).
    current_price (float): The current price of the asset.
    price_data (deque): Price history data (deque).
    volume_data (deque): Volume history data (deque).
    current_time (datetime): Current time to track lows.
    
    Returns:
    str: Signal message if generated, else False.
    """

    # Initialize the recent_lows for the pair if it doesn't exist
    if pair not in recent_lows:
        recent_lows[pair] = deque(maxlen=3)

    logging.info(f"Checking lows for {pair}. Current price: {current_price}, Time: {current_time}")

    # Ensure that we have at least 2 price points before comparing current price
    if len(price_data) >= 2:
        previous_low_price = min([low['price'] for low in recent_lows[pair]]) if recent_lows[pair] else None

        # Check if current price is significantly lower than the last recorded low (threshold of 0.5%)
        if previous_low_price is not None and current_price >= previous_low_price * (1 - PRICE_DIFF_THRESHOLD):
            logging.info(f"Price did not drop significantly (less than {PRICE_DIFF_THRESHOLD * 100}% from the previous low), skipping.")
            return False  # Skip adding new low and signal generation if the price doesn't meet the threshold

        # Calculate RSI if we have at least 14 prices
        rsi = calculate_rsi(list(price_data)) if len(price_data) >= 14 else None

        # Safeguard for volume data to avoid issues if any volumes are missing
        current_volume = volume_data[-1] if len(volume_data) > 0 else None

        if current_volume is not None:
            # Log and add the new low if it meets the price difference condition
            logging.info(f"Adding new low for {pair}. Price: {current_price}, Volume: {current_volume}, RSI: {rsi}")
            recent_lows[pair].append({
                'price': current_price,
                'volume': current_volume,
                'rsi': rsi,
                'time': current_time
            })

            # Now that we have added a new low, check the conditions
            if len(recent_lows[pair]) == 3:
                # Extract volumes for the 3 lows
                volumes = [low['volume'] for low in recent_lows[pair]]
                avg_volume = sum(volumes) / len(volumes) if len(volumes) > 0 else 1  # Prevent division by zero

                logging.info(f"Average volume for {pair}: {avg_volume}, Volumes at lows: {volumes}")

                # Volume condition: volumes should be greater than 1.5x average and decreasing
                volume_condition = all(v > avg_volume * HIGH_VOLUME_THRESHOLD for v in volumes) and volumes[0] > volumes[1] > volumes[2]

                # RSI condition: RSI 3 should be higher than RSI 1 and RSI 2, but RSI 1 and RSI 2 must be between 1-40
                rsis = [low['rsi'] for low in recent_lows[pair] if low['rsi'] is not None]
                rsi_condition = (
                    len(rsis) == 3 and 1 <= rsis[0] <= 40 and 1 <= rsis[1] <= 40 and rsis[2] > rsis[0] and rsis[2] > rsis[1]
                )

                # Generate signal if either volume condition or RSI condition is satisfied
                if volume_condition or rsi_condition:
                    # Calculate entry price and stop loss based on 1:2 reward-to-risk ratio
                    entry_price = current_price
                    stop_loss = entry_price - (entry_price * 0.068)  # Example stop loss (6.8% below entry)
                    stop_loss, tp1, tp2, tp3 = calculate_reward_risk(entry_price, stop_loss)

                    signal_message = (
                        f"⚠️ NEW Signal DETECTED - 3rd Low!\n\n"
                        f"PAIR: {pair}\n"
                        f"Price: ${current_price:.4f}\n\n"
                        f"🟢Entry Price:  ${entry_price:.4f}\n"
                        f"❌Stop Loss: ${stop_loss:.2f}\n\n"
                        f"TP1: ${tp1:.2f}\n"
                        f"TP2: ${tp2:.2f}\n"
                        f"TP3: ${tp3:.2f}\n\n"
                        f"Time: {current_time}\n\n"
                        f"Previous Lows:\n"
                        f"- Low 1: ${recent_lows[pair][0]['price']:.4f} (Volume: {format_volume(recent_lows[pair][0]['volume'])}, RSI: {recent_lows[pair][0]['rsi']:.2f})\n"
                        f"- Low 2: ${recent_lows[pair][1]['price']:.4f} (Volume: {format_volume(recent_lows[pair][1]['volume'])}, RSI: {recent_lows[pair][1]['rsi']:.2f})\n"
                        f"- Low 3: ${recent_lows[pair][2]['price']:.4f} (Volume: {format_volume(recent_lows[pair][2]['volume'])}, RSI: {recent_lows[pair][2]['rsi']:.2f})\n\n"
                        f"Volume trend: {'Decreasing' if volume_condition else 'Not decreasing'}\n"
                        f"RSI trend: {'RSI increasing and in range (1-40) with RSI3 > RSI1 & RSI2' if rsi_condition else 'No RSI signal'}\n"
                    )
                    logging.info(f"Signal Generated for {pair}: {signal_message}")
                    return signal_message

    logging.info(f"No signal generated for {pair}.")
    return False
