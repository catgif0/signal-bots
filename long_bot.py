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
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}  # Store up to 60 prices (one price per minute)
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}  # Store up to 60 volume data points (one volume per minute)

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    for symbol in SYMBOLS:
        try:
            logging.info(f"Fetching OI, price, and volume data for {symbol}.")

            # Fetch OI changes for the symbol from your existing logic
            oi_1m = get_open_interest_change(symbol, '1m')
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            logging.debug(f"OI Data for {symbol}: 1m={oi_1m}, 5m={oi_5m}, 15m={oi_15m}, 1h={oi_1h}, 24h={oi_24h}")

            # Fetch current price data
            price_data = get_price_data(symbol)
            current_price = price_data.get("price", None)

            # Append current price and volume to history
            price_history[symbol].append(current_price)

            # Ensure enough historical data is present in deque before calculating changes
            price_change_1m = ((current_price - price_history[symbol][-2]) / price_history[symbol][-2]) * 100 if len(price_history[symbol]) >= 2 else None

            # Fetch volume changes for the symbol
            current_volume = get_volume(symbol)
            volume_history[symbol].append(current_volume)
            volume_change_1m = ((current_volume - volume_history[symbol][-2]) / volume_history[symbol][-2]) * 100 if len(volume_history[symbol]) >= 2 else None

            logging.debug(f"Price changes for {symbol}: 1m={price_change_1m}")
            logging.debug(f"Volume changes for {symbol}: 1m={volume_change_1m}")

            # Create dictionaries of OI, price, and volume changes for the symbol
            oi_changes = {"1m": oi_1m, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
            price_changes = {"1m": price_change_1m}
            volume_changes = {"1m": volume_change_1m}

            # Check if conditions for signal generation are met
            signal = generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes)

            # If a signal is generated, send it via Telegram
            if signal:
                logging.info(f"Signal generated for {symbol}: {signal}")
                send_telegram_message(signal)
            else:
                logging.info(f"No signal generated for {symbol} during this iteration.")

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
