import time
import logging
from collections import deque
from services.signal_generation import generate_signal
from services.telegram import send_telegram_message
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 
           'ORBSUSDT', 'ARKUSDT', 'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

# Data history for price, volume, and OI changes
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
oi_history = {symbol: deque(maxlen=2) for symbol in SYMBOLS}  # Store last two OI values for calculating 1m change

# Function to calculate the OI change from the previous minute
def calculate_oi_change(symbol):
    if len(oi_history[symbol]) == 2:
        return ((oi_history[symbol][-1] - oi_history[symbol][-2]) / oi_history[symbol][-2]) * 100
    return None

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    
    for symbol in SYMBOLS:
        try:
            logging.info(f"Fetching OI, price, and volume data for {symbol}.")
            
            # Fetch OI changes for different timeframes
            current_oi = get_open_interest_change(symbol, '1m')  # Assume this is the current OI for the pair
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            # Append the current OI to the history to calculate 1-minute OI change
            oi_history[symbol].append(current_oi)
            oi_1m = calculate_oi_change(symbol)  # Calculate the 1m OI change

            # Fetch price data
            price_data = get_price_data(symbol)
            current_price = price_data.get("price", None)
            price_change_24h = price_data.get("price_change_24h", None)
            
            # Append current price to history
            price_history[symbol].append(current_price)

            # Format current price to four decimal places
            formatted_price = f"{current_price:.4f}" if current_price is not None else "N/A"

            # Fetch volume data
            current_volume = get_volume(symbol)
            volume_history[symbol].append(current_volume)

            # Calculate price and volume changes (with safe fallback to None)
            price_change_1m = ((current_price - price_history[symbol][-2]) / price_history[symbol][-2]) * 100 if len(price_history[symbol]) >= 2 else None
            price_change_5m = ((current_price - price_history[symbol][-5]) / price_history[symbol][-5]) * 100 if len(price_history[symbol]) >= 5 else None
            price_change_15m = ((current_price - price_history[symbol][-15]) / price_history[symbol][-15]) * 100 if len(price_history[symbol]) >= 15 else None
            price_change_1h = ((current_price - price_history[symbol][-60]) / price_history[symbol][-60]) * 100 if len(price_history[symbol]) >= 60 else None

            volume_change_1m = ((current_volume - volume_history[symbol][-2]) / volume_history[symbol][-2]) * 100 if len(volume_history[symbol]) >= 2 else None
            volume_change_5m = ((current_volume - volume_history[symbol][-5]) / volume_history[symbol][-5]) * 100 if len(volume_history[symbol]) >= 5 else None
            volume_change_15m = ((current_volume - volume_history[symbol][-15]) / volume_history[symbol][-15]) * 100 if len(volume_history[symbol]) >= 15 else None
            volume_change_1h = ((current_volume - volume_history[symbol][-60]) / volume_history[symbol][-60]) * 100 if len(volume_history[symbol]) >= 60 else None
            
            # Log all fetched data
            logging.info(f"Symbol: {symbol}, Current Price: {formatted_price}, OI 1m: {oi_1m}, OI 5m: {oi_5m}, OI 15m: {oi_15m}, OI 1h: {oi_1h}, OI 24h: {oi_24h}")
            logging.info(f"Price Changes: 1m={price_change_1m}, 5m={price_change_5m}, 15m={price_change_15m}, 1h={price_change_1h}, 24h={price_change_24h}")
            logging.info(f"Volume Changes: 1m={volume_change_1m}, 5m={volume_change_5m}, 15m={volume_change_15m}, 1h={volume_change_1h}")

            # Check if conditions for signal generation are met
            oi_changes = {"1m": oi_1m, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
            price_changes = {"1m": price_change_1m, "5m": price_change_5m, "15m": price_change_15m, "1h": price_change_1h, "24h": price_change_24h}
            volume_changes = {"1m": volume_change_1m, "5m": volume_change_5m, "15m": volume_change_15m, "1h": volume_change_1h}
            
            signal = generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes)

            # Log whether a signal was generated
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
