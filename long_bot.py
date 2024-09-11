import time
import logging
from collections import deque
from services.signal_generation import generate_signal  # Existing signal logic
from services.new_signal_generation import generate_new_signal  # New signal logic
from services.telegram import send_telegram_message
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Symbols to monitor
SYMBOLS = ['BTCUSDT', 'ETHUSDT', 'MANAUSDT', 'CRVUSDT', 'STRKUSDT', 'DARUSDT', 'BIGTIMEUSDT', 
           'NKNUSDT', 'OMGUSDT', 'RIFUSDT', 'AVAXUSDT', 'HOOKUSDT', 'TRBUSDT', 'VIDTUSDT']

# Price, volume, and OI history to track changes over time intervals
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
oi_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}

# Recent lows tracking for the new signal generation logic
recent_lows = {symbol: deque(maxlen=3) for symbol in SYMBOLS}

# Function to safely calculate changes
def safe_calculate(change, old_value):
    if change is None or old_value is None:
        return None
    try:
        return (change - old_value) / old_value * 100
    except (ZeroDivisionError, TypeError):
        return None

# Function to update lows with new low logic
def update_lows(pair, current_price, current_volume, current_time):
    """
    Update the recent lows with the new price if it's lower than the highest of the current lows.
    Then sort the lows to ensure Low 1 is the highest and Low 3 is the lowest.
    """
    if len(recent_lows[pair]) < 3:
        recent_lows[pair].append({
            'price': current_price,
            'volume': current_volume,
            'time': current_time
        })
    else:
        # Replace the highest low if the current price is lower
        highest_low = max(recent_lows[pair], key=lambda x: x['price'])
        if current_price < highest_low['price']:
            highest_index = recent_lows[pair].index(highest_low)
            recent_lows[pair][highest_index] = {
                'price': current_price,
                'volume': current_volume,
                'time': current_time
            }

    # Sort lows by price, ensuring Low 1 is highest and Low 3 is lowest
    recent_lows[pair] = deque(sorted(recent_lows[pair], key=lambda x: x['price'], reverse=True), maxlen=3)

    logging.info(f"Updated recent lows for {pair}: {recent_lows[pair]}")

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    
    for symbol in SYMBOLS:
        try:
            logging.info(f"Fetching OI, price, and volume data for {symbol}.")
            
            # Fetch OI changes for different intervals
            oi_current = get_open_interest_change(symbol, '5m')  # Assuming OI for 5m is the smallest interval available
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            # Append the current OI to history and calculate the 1m OI change dynamically
            oi_history[symbol].append(oi_current)
            if len(oi_history[symbol]) >= 2:
                oi_1m_change = safe_calculate(oi_history[symbol][-1], oi_history[symbol][-2])
            else:
                oi_1m_change = None

            # Fetch price data
            price_data = get_price_data(symbol)
            current_price = price_data.get("price", None)
            price_change_24h = price_data.get("price_change_24h", None)
            
            if current_price is None:
                logging.warning(f"Price data for {symbol} is None, skipping.")
                continue
            
            price_history[symbol].append(current_price)
            formatted_price = f"{current_price:.4f}"

            # Fetch volume data
            current_volume = get_volume(symbol)
            if current_volume is None:
                logging.warning(f"Volume data for {symbol} is None, skipping.")
                continue
            volume_history[symbol].append(current_volume)

            # Calculate price and volume changes
            price_change_1m = safe_calculate(current_price, price_history[symbol][-2]) if len(price_history[symbol]) >= 2 else None
            price_change_5m = safe_calculate(current_price, price_history[symbol][-5]) if len(price_history[symbol]) >= 5 else None
            price_change_15m = safe_calculate(current_price, price_history[symbol][-15]) if len(price_history[symbol]) >= 15 else None
            price_change_1h = safe_calculate(current_price, price_history[symbol][-60]) if len(price_history[symbol]) >= 60 else None

            volume_change_1m = safe_calculate(current_volume, volume_history[symbol][-2]) if len(volume_history[symbol]) >= 2 else None
            volume_change_5m = safe_calculate(current_volume, volume_history[symbol][-5]) if len(volume_history[symbol]) >= 5 else None
            volume_change_15m = safe_calculate(current_volume, volume_history[symbol][-15]) if len(volume_history[symbol]) >= 15 else None
            volume_change_1h = safe_calculate(current_volume, volume_history[symbol][-60]) if len(volume_history[symbol]) >= 60 else None
            
            # Log all fetched data
            logging.info(f"Symbol: {symbol}, Current Price: {formatted_price}, OI 1m Change: {oi_1m_change}, OI 5m: {oi_5m}, OI 15m: {oi_15m}, OI 1h: {oi_1h}, OI 24h: {oi_24h}")
            logging.info(f"Price Changes: 1m={price_change_1m}, 5m={price_change_5m}, 15m={price_change_15m}, 1h={price_change_1h}, 24h={price_change_24h}")
            logging.info(f"Volume Changes: 1m={volume_change_1m}, 5m={volume_change_5m}, 15m={volume_change_15m}, 1h={volume_change_1h}")

            # Check if conditions for original signal generation are met
            oi_changes = {"1m": oi_1m_change, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
            price_changes = {"1m": price_change_1m, "5m": price_change_5m, "15m": price_change_15m, "1h": price_change_1h, "24h": price_change_24h}
            volume_changes = {"1m": volume_change_1m, "5m": volume_change_5m, "15m": volume_change_15m, "1h": volume_change_1h}
            
            # Call original signal generation logic
            signal = generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes)

            # Call the new signal generation logic
            update_lows(symbol, current_price, current_volume, time.time())  # Update recent lows
            new_signal = generate_new_signal(symbol, current_price, price_history[symbol], volume_history[symbol], time.time())

            # Log whether a signal was generated from either logic
            if signal:
                logging.info(f"Signal generated for {symbol}: {signal}")
                send_telegram_message(signal)
            if new_signal:
                logging.info(f"New Signal generated for {symbol}: {new_signal}")
                send_telegram_message(new_signal)
        
        except Exception as e:
            logging.error(f"Error while processing {symbol}: {e}")

    logging.info("Monitoring completed for this iteration.")

# Call the monitor_pairs function every minute
if __name__ == "__main__":
    while True:
        logging.info("Starting new monitoring cycle.")
        monitor_pairs()
        logging.info("Sleeping for 60 seconds before next cycle.")
        time.sleep(60)
