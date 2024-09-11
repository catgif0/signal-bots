import logging
from collections import deque
from services.signal_generation import calculate_take_profit, calculate_stop_loss
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# High volume threshold for new lows signal
HIGH_VOLUME_THRESHOLD = 1.5  # 1.5x of the average volume
recent_lows = {}  # Track up to 3 recent lows with volume for each symbol

# New signal generation logic based on three lows and decreasing volume trend
def generate_new_signal(pair, current_price, price_data, volume_data, current_time):
    """
    Signal generation logic based on:
    1. Three new lows with decreasing volume trend.
    
    Args:
    pair: str: The pair being analyzed (e.g., BTCUSDT)
    current_price: float: The current price of the asset
    price_data: deque: Price history data (deque)
    volume_data: deque: Volume history data (deque, specifically 1-minute volumes)
    current_time: float: Current time (as a Unix timestamp) to track lows
    
    Returns:
    str: Signal message if generated, else False
    """

    # Initialize the low tracking deque for the pair if not present
    if pair not in recent_lows:
        recent_lows[pair] = deque(maxlen=3)

    logging.info(f"Checking lows for {pair}. Current price: {current_price}, Time: {current_time}")

    # Only proceed if there is enough price history
    if len(price_data) >= 2:
        # Check if the current price is a new low compared to the recent lows
        if not recent_lows[pair] or current_price < min([low['price'] for low in recent_lows[pair]]):
            # Log and append the new low with the corresponding volume (assumed to be 1-minute volume)
            logging.info(f"Adding new low for {pair}. Price: {current_price}, Volume: {volume_data[-1]}")
            recent_lows[pair].append({
                'price': current_price,
                'volume': volume_data[-1],  # Using the latest 1-minute volume
                'time': current_time
            })

    # Log the recent lows for debugging purposes
    if len(recent_lows[pair]) > 0:
        logging.info(f"Recent lows for {pair}:")
        for idx, low in enumerate(recent_lows[pair], 1):
            logging.info(f"Low {idx}: Price: {low['price']}, Volume: {low['volume']}, Time: {low['time']}")

    # Check if we have 3 new lows and a decreasing volume trend
    if len(recent_lows[pair]) == 3:
        # Extract the volumes at each of the three recent lows
        volumes = [low['volume'] for low in recent_lows[pair]]
        
        # Calculate the average volume (this should be 1-minute volumes)
        avg_volume = sum(volume_data[-5:]) / len(volume_data[-5:]) if len(volume_data) >= 5 else sum(volume_data) / len(volume_data)
        logging.info(f"Average volume for {pair} (last 5 mins): {avg_volume}, Volumes at lows: {volumes}")

        # Check for the volume threshold and a decreasing pattern in volume
        if all(v > avg_volume * HIGH_VOLUME_THRESHOLD for v in volumes) and volumes[0] > volumes[1] > volumes[2]:
            # Generate the signal if the conditions are met
            signal_message = (
                f"⚠️ NEW LOW DETECTED - 3rd Low!\n\n"
                f"PAIR: {pair}\n"
                f"Price: ${current_price:.4f}\n"
                f"Time: {current_time}\n\n"
                f"Previous Lows:\n"
                f"- Low 1: ${recent_lows[pair][0]['price']:.4f} (Volume: {recent_lows[pair][0]['volume']})\n"
                f"- Low 2: ${recent_lows[pair][1]['price']:.4f} (Volume: {recent_lows[pair][1]['volume']})\n"
                f"- Low 3: ${recent_lows[pair][2]['price']:.4f} (Volume: {recent_lows[pair][2]['volume']})\n\n"
                f"Volume trend: Decreasing (High volumes but reducing at each low)\n"
            )
            logging.info(f"Signal Generated for {pair}: {signal_message}")
            return signal_message

    # Log when no signal is generated
    logging.info(f"No signal generated for {pair}.")
    return False
