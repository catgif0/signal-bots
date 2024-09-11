import logging
from collections import deque
from services.rsi_calculation import calculate_rsi  # Import RSI calculation function
from services.signal_generation import calculate_take_profit, calculate_stop_loss
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# High volume threshold for new lows signal
HIGH_VOLUME_THRESHOLD = 1.5  # 1.5x of the average volume
recent_lows = {}  # Track up to 3 recent lows with volume and RSI for each symbol

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
        if not recent_lows[pair] or current_price < min([low['price'] for low in recent_lows[pair]]):
            # Calculate RSI if we have at least 14 prices
            rsi = calculate_rsi(list(price_data)) if len(price_data) >= 14 else None

            # Safeguard for volume data to avoid issues if any volumes are missing
            current_volume = volume_data[-1] if len(volume_data) > 0 else None

            if current_volume is not None:
                # Log current low, volume, and RSI before appending to recent_lows
                logging.info(f"Adding new low for {pair}. Price: {current_price}, Volume: {current_volume}, RSI: {rsi}")
                recent_lows[pair].append({
                    'price': current_price,
                    'volume': current_volume,
                    'rsi': rsi,
                    'time': current_time
                })

    # Log the details of the recent lows
    if len(recent_lows[pair]) > 0:
        logging.info(f"Recent lows for {pair}:")
        for idx, low in enumerate(recent_lows[pair], 1):
            logging.info(f"Low {idx}: Price: {low['price']}, Volume: {low['volume']}, RSI: {low['rsi']}, Time: {low['time']}")

    # Check if we have 3 new lows and either decreasing volume trend or oversold RSI
    if len(recent_lows[pair]) == 3:
        # Extract volumes for the 3 lows
        volumes = [low['volume'] for low in recent_lows[pair]]
        avg_volume = sum(volumes) / len(volumes) if len(volumes) > 0 else 1  # Prevent division by zero

        logging.info(f"Average volume for {pair}: {avg_volume}, Volumes at lows: {volumes}")

        # Volume condition: volumes should be greater than 1.5x average and decreasing
        volume_condition = all(v > avg_volume * HIGH_VOLUME_THRESHOLD for v in volumes) and volumes[0] > volumes[1] > volumes[2]

        # RSI condition: RSI 3 should be higher than RSI 1 and RSI 2, but RSI 1 and RSI 2 must be between 1-40
        # NEW: Updated logic to ensure RSI 3 is greater than RSI 1 and RSI 2, and RSI 1 and 2 must be between 1-40.
        rsis = [low['rsi'] for low in recent_lows[pair] if low['rsi'] is not None]
        rsi_condition = (
            len(rsis) == 3 and 1 <= rsis[0] <= 40 and 1 <= rsis[1] <= 40 and rsis[2] > rsis[0] and rsis[2] > rsis[1]
        )  # NEW: Ensures RSI3 is the highest, but RSI1 and RSI2 can be in any positive or negative ratio within 1-40.

        # Generate signal if either volume condition or RSI condition is satisfied
        if volume_condition or rsi_condition:
            signal_message = (
                f"⚠️ NEW LOW DETECTED - 3rd Low!\n\n"
                f"PAIR: {pair}\n"
                f"Price: ${current_price:.4f}\n"
                f"Time: {current_time}\n\n"
                f"Previous Lows:\n"
                f"- Low 1: ${recent_lows[pair][0]['price']:.4f} (Volume: {recent_lows[pair][0]['volume']}, RSI: {recent_lows[pair][0]['rsi']})\n"
                f"- Low 2: ${recent_lows[pair][1]['price']:.4f} (Volume: {recent_lows[pair][1]['volume']}, RSI: {recent_lows[pair][1]['rsi']})\n"
                f"- Low 3: ${recent_lows[pair][2]['price']:.4f} (Volume: {recent_lows[pair][2]['volume']}, RSI: {recent_lows[pair][2]['rsi']})\n\n"
                f"Volume trend: {'Decreasing' if volume_condition else 'Not decreasing'}\n"
                f"RSI trend: {'RSI increasing and in range (1-40) with RSI3 > RSI1 & RSI2' if rsi_condition else 'No RSI signal'}\n"  # NEW: Updated RSI trend description.
            )
            logging.info(f"Signal Generated for {pair}: {signal_message}")
            return signal_message

    logging.info(f"No signal generated for {pair}.")
    return False
