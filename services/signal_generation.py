import logging
from collections import deque

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Example thresholds for signal generation
THRESHOLDS = {
    'OI': {'1m': 1.0},  # OI change threshold for 1m
    'Price': {'1m': 0.5},  # Price change threshold for 1m
    'Volume': {'1m': 20.0}  # Volume change threshold for 1m (20% increase)
}

HIGH_VOLUME_THRESHOLD = 1.5  # 1.5x of the average volume
recent_lows = deque(maxlen=3)  # Track up to 3 recent lows with volume

# Example take-profit and stop-loss calculations
def calculate_take_profit(current_price, reward_ratio=2):
    return [current_price + current_price * 0.02 * i for i in range(1, 4)]

def calculate_stop_loss(current_price):
    return current_price * 0.98

# Signal generation logic
def generate_signal(pair, current_price, oi_changes, price_changes, volume_changes, price_data, volume_data, current_time):
    """
    Signal generation logic based on:
    1. OI, price, and volume changes
    2. Three new lows with decreasing volume trend
    
    Args:
    pair: str: The pair being analyzed (e.g., BTCUSDT)
    current_price: float: The current price of the asset
    oi_changes: dict: Dictionary containing OI changes for different timeframes (1m, 5m, 15m, 1h, 24h)
    price_changes: dict: Dictionary containing price changes for different timeframes
    volume_changes: dict: Dictionary containing volume changes for different timeframes
    price_data: deque: Price history data (deque)
    volume_data: deque: Volume history data (deque)
    current_time: datetime: Current time to track lows
    
    Returns:
    str: Signal message if generated, else False
    """

    # ---------- Track new lows and volume ----------
    if len(price_data) >= 2:
        if not recent_lows or current_price < min([low['price'] for low in recent_lows]):
            recent_lows.append({
                'price': current_price,
                'volume': volume_changes['1m'],
                'time': current_time
            })
            logging.info(f"New low identified for {pair}: Price: {current_price}, Volume: {volume_changes['1m']}")

    # Log details of the three lows if available
    if len(recent_lows) == 3:
        logging.info(f"Three recent lows for {pair}:")
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

    # ---------- Original signal generation logic based on OI, price, and volume ----------
    if oi_changes['1m'] is not None and oi_changes['1m'] > THRESHOLDS['OI']['1m']:
        if all(oi_changes.get(tf, 0) < 0 for tf in ['5m', '15m', '1h', '24h']):
            if price_changes['1m'] is not None and price_changes['1m'] > THRESHOLDS['Price']['1m']:
                if volume_changes['1m'] is not None and volume_changes['1m'] > THRESHOLDS['Volume']['1m']:
                    stop_loss = calculate_stop_loss(current_price)
                    take_profit = calculate_take_profit(current_price)
                    signal_message = (
                        f"STEP 1: INITIAL REVERSAL SPOTTED (1m Data)!\n\n"
                        f"PAIR: {pair}\n"
                        f"Price: ${current_price:.4f}\n"
                        f"Stop Loss: ${stop_loss:.4f}\n"
                        f"TP1: ${take_profit[0]:.4f}, TP2: ${take_profit[1]:.4f}, TP3: ${take_profit[2]:.4f}\n\n"
                        f"🔴 #{pair} ${current_price:.4f} | OI changed in 1m\n\n"
                        f"┌ 🌐 Open Interest \n"
                        f"├ 🟩{oi_changes['1m']:.4f}% (1m)\n"
                        f"├ 🟥{oi_changes['5m']:.4f}% (5m)\n"
                        f"├ 🟥{oi_changes['15m']:.4f}% (15m)\n"
                        f"├ 🟥{oi_changes['1h']:.4f}% (1h)\n"
                        f"└ 🟥{oi_changes['24h']:.4f}% (24h)\n\n"
                        f"┌ 📈 Price change \n"
                        f"├ 🟩{price_changes['1m']:.4f}% (1m)\n"
                        f"└ Volume change 🟩{volume_changes['1m']:.4f}% (1m)"
                    )
                    logging.info(f"Signal Generated: {signal_message}")
                    return signal_message

    logging.info(f"No signal generated for {pair}.")
    return False
