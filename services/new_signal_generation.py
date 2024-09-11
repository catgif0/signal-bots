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

    if pair not in recent_lows:
        recent_lows[pair] = deque(maxlen=3)

    logging.info(f"Checking lows for {pair}. Current price: {current_price}, Time: {current_time}")

    if len(price_data) >= 2:
        if not recent_lows[pair] or current_price < min([low['price'] for low in recent_lows[pair]]):
            # Calculate RSI if enough data exists (at least 14 prices)
            rsi = calculate_rsi(list(price_data)) if len(price_data) >= 14 else None

            # Log current low, volume, and RSI before appending
            logging.info(f"Adding new low for {pair}. Price: {current_price}, Volume: {volume_data[-1]}, RSI: {rsi}")
            recent_lows[pair].append({
                'price': current_price,
                'volume': volume_data[-1],
                'rsi': rsi,
                'time': current_time
            })

    # Log details of the recent lows every time, even if a signal is not generated
    if len(recent_lows[pair]) > 0:
        logging.info(f"Recent lows for {pair}:")
        for idx, low in enumerate(recent_lows[pair], 1):
            logging.info(f"Low {idx}: Price: {low['price']}, Volume: {low['volume']}, RSI: {low['rsi']}, Time: {low['time']}")

    # Check if we have 3 new lows and either decreasing volume trend or oversold RSI
    if len(recent_lows[pair]) == 3:
        # Check volume condition
        volumes = [low['volume'] for low in recent_lows[pair]]
        avg_volume = sum(volume_data) / len(volume_data) if len(volume_data) > 0 else 1  # Avoid division by zero
        logging.info(f"Average volume for {pair}: {avg_volume}, Volumes at lows: {volumes}")
        
        volume_condition = all(v > avg_volume * HIGH_VOLUME_THRESHOLD for v in volumes) and volumes[0] > volumes[1] > volumes[2]

        # Check RSI condition (e.g., RSI < 30 implies oversold)
        rsis = [low['rsi'] for low in recent_lows[pair] if low['rsi'] is not None]
        rsi_condition = all(rsi < 30 for rsi in rsis) if len(rsis) == 3 else False

        # Signal is generated if either volume condition or RSI condition is true
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
                f"RSI trend: {'Oversold (RSI < 30)' if rsi_condition else 'No RSI signal'}\n"
            )
            logging.info(f"Signal Generated for {pair}: {signal_message}")
            return signal_message

    logging.info(f"No signal generated for {pair}.")
    return False
