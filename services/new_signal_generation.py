import logging
from collections import deque
from services.signal_generation import calculate_take_profit, calculate_stop_loss
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# High volume threshold for new lows signal
HIGH_VOLUME_THRESHOLD = 1.5  # 1.5x of the average volume
recent_lows = deque(maxlen=3)  # Track up to 3 recent lows with volume

# New signal generation logic based on three lows and decreasing volume trend
def generate_new_signal(pair, current_price, price_data, volume_data, current_time):
    """
    Signal generation logic based on:
    1. Three new lows with decreasing volume trend.
    
    Args:
    pair: str: The pair being analyzed (e.g., BTCUSDT)
    current_price: float: The current price of the asset
    price_data: deque: Price history data (deque)
    volume_data: deque: Volume history data (deque)
    current_time: datetime: Current time to track lows
    
    Returns:
    str: Signal message if generated, else False
    """

    # ---------- Track new lows and volume ----------
    logging.info(f"Checking lows for {pair}. Current price: {current_price}, Time: {current_time}")

    if len(price_data) >= 2:
        if not recent_lows or current_price < min([low['price'] for low in recent_lows]):
            recent_lows.append({
                'price': current_price,
                'volume': volume_data[-1],
                'time': current_time
            })
            logging.info(f"New low identified for {pair}: Price: {current_price}, Volume: {volume_data[-1]}")

    # Log details of the recent lows every time, even if a signal is not generated
    if len(recent_lows) > 0:
        logging.info(f"Recent lows for {pair}:")
        for idx, low in enumerate(recent_lows, 1):
            logging.info(f"Low {idx}: Price: {low['price']}, Volume: {low['volume']}, Time: {low['time']}")

    # Check if we have 3 new lows and decreasing volume trend
    if len(recent_lows) == 3:
        volumes = [low['volume'] for low in recent_lows]
        avg_volume = sum(volume_data) / len(volume_data) if len(volume_data) > 0 else 1  # Avoid division by zero
        if all(v > avg_volume * HIGH_VOLUME_THRESHOLD for v in volumes) and volumes[0] > volumes[1] > volumes[2]:
            signal_message = (
                f"⚠️ NEW LOW DETECTED - 3rd Low!\n\n"
                f"PAIR: {pair}\n"
                f"Price: ${current_price:.4f}\n"
                f"Time: {current_time}\n\n"
                f"Previous Lows:\n"
                f"- Low 1: ${recent_lows[0]['price']:.4f} (Volume: {recent_lows[0]['volume']})\n"
                f"- Low 2: ${recent_lows[1]['price']:.4f} (Volume: {recent_lows[1]['volume']})\n"
                f"- Low 3: ${recent_lows[2]['price']:.4f} (Volume: {recent_lows[2]['volume']})\n\n"
                f"Volume trend: Decreasing (High volumes but reducing at each low)\n"
            )
            logging.info(f"Signal Generated for {pair}: {signal_message}")
            return signal_message

    logging.info(f"No signal generated for {pair}.")
    return False
