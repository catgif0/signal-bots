import time
import logging
from collections import deque
from services.signal_generation import generate_signal
from services.telegram import send_telegram_message
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 'ORBSUSDT', 'ARKUSDT', 
           'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

# Price and volume history to track changes over time intervals
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}

# Safely compare values and log issues
def safe_compare(value1, value2, comparison_operator):
    if value1 is None or value2 is None:
        logging.error(f"Comparison error: One of the values is None (value1: {value1}, value2: {value2})")
        return False
    return comparison_operator(value1, value2)

# Function to log all data whether signal is generated or not
def log_oi_price_volume(symbol, oi_data, price_data, volume_data):
    logging.info(f"PAIR: {symbol}")
    logging.info(f"Price: {price_data.get('price', 'N/A')}")
    logging.info(f"OI 1m: {oi_data['1m']}, OI 5m: {oi_data['5m']}, OI 15m: {oi_data['15m']}, OI 1h: {oi_data['1h']}, OI 24h: {oi_data['24h']}")
    logging.info(f"Volume 1m: {volume_data['1m']}, Volume 5m: {volume_data['5m']}, Volume 15m: {volume_data['15m']}, Volume 1h: {volume_data['1h']}")

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    for symbol in SYMBOLS:
        try:
            # Fetch OI, price, and volume data
            logging.info(f"Fetching OI, price, and volume data for {symbol}.")
            oi_1m = get_open_interest_change(symbol, '1m')
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            price_data = get_price_data(symbol)
            current_price = price_data.get("price", None)

            if current_price is not None:
                price_history[symbol].append(current_price)

            # Ensure enough historical data is present in deque before calculating changes
            price_change_1m = ((current_price - price_history[symbol][-2]) / price_history[symbol][-2]) * 100 if len(price_history[symbol]) >= 2 else None
            price_change_5m = ((current_price - price_history[symbol][-5]) / price_history[symbol][-5]) * 100 if len(price_history[symbol]) >= 5 else None
            price_change_15m = ((current_price - price_history[symbol][-15]) / price_history[symbol][-15]) * 100 if len(price_history[symbol]) >= 15 else None
            price_change_1h = ((current_price - price_history[symbol][-60]) / price_history[symbol][-60]) * 100 if len(price_history[symbol]) >= 60 else None
            price_change_24h = price_data.get("price_change_24h", None)

            current_volume = get_volume(symbol)
            if current_volume is not None:
                volume_history[symbol].append(current_volume)

            volume_change_1m = ((current_volume - volume_history[symbol][-2]) / volume_history[symbol][-2]) * 100 if len(volume_history[symbol]) >= 2 else None
            volume_change_5m = ((current_volume - volume_history[symbol][-5]) / volume_history[symbol][-5]) * 100 if len(volume_history[symbol]) >= 5 else None
            volume_change_15m = ((current_volume - volume_history[symbol][-15]) / volume_history[symbol][-15]) * 100 if len(volume_history[symbol]) >= 15 else None
            volume_change_1h = ((current_volume - volume_history[symbol][-60]) / volume_history[symbol][-60]) * 100 if len(volume_history[symbol]) >= 60 else None

            oi_data = {'1m': oi_1m, '5m': oi_5m, '15m': oi_15m, '1h': oi_1h, '24h': oi_24h}
            price_changes = {'1m': price_change_1m, '5m': price_change_5m, '15m': price_change_15m, '1h': price_change_1h, '24h': price_change_24h}
            volume_changes = {'1m': volume_change_1m, '5m': volume_change_5m, '15m': volume_change_15m, '1h': volume_change_1h}

            # Log data for every symbol during monitoring
            log_oi_price_volume(symbol, oi_data, price_changes, volume_changes)

            # Generate signal based on current data
            signal = generate_signal(symbol, current_price, oi_data, price_changes, volume_changes)

            if signal:
                logging.info(f"Signal generated for {symbol}: {signal}")
                send_telegram_message(signal)
            else:
                logging.info(f"No signal generated for {symbol} during this iteration.")

        except Exception as e:
            logging.error(f"Error while processing {symbol}: {e}")

    logging.info("Monitoring completed for this iteration.")

# Run the monitoring cycle every minute
if __name__ == "__main__":
    while True:
        logging.info("Starting new monitoring cycle.")
        monitor_pairs()
        logging.info("Sleeping for 60 seconds before next cycle.")
        time.sleep(60)
