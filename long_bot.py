import time
import logging
from services.signal_generation import generate_signal
from services.telegram import send_telegram_message
from services.binance_api import get_open_interest_change, get_price_data, get_volume

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 'ORBSUSDT', 'ARKUSDT', 'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

# Function to monitor pairs and log data
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    for symbol in SYMBOLS:
        try:
            logging.info(f"Fetching OI, price, and volume data for {symbol}.")

            # Fetch data
            oi_1m = get_open_interest_change(symbol, '1m')
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            price_data = get_price_data(symbol)
            current_price = price_data.get("price")

            volume_1m = get_volume(symbol, '1m')
            volume_5m = get_volume(symbol, '5m')
            volume_15m = get_volume(symbol, '15m')
            volume_1h = get_volume(symbol, '1h')

            # Log the fetched data
            logging.info(f"PAIR: {symbol}")
            logging.info(f"Price: {current_price if current_price is not None else 'N/A'}")
            logging.info(f"OI 1m: {oi_1m}, OI 5m: {oi_5m}, OI 15m: {oi_15m}, OI 1h: {oi_1h}, OI 24h: {oi_24h}")
            logging.info(f"Volume 1m: {volume_1m}, Volume 5m: {volume_5m}, Volume 15m: {volume_15m}, Volume 1h: {volume_1h}")

            # Validate if data exists before further comparisons
            if current_price is None or oi_1m is None or volume_1m is None:
                logging.warning(f"Skipping {symbol} due to missing data.")
                continue  # Skip this pair if essential data is missing

            # Prepare the data for signal generation
            oi_changes = {"1m": oi_1m, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
            price_changes = {"1m": price_data.get("price_change_1m"), "5m": price_data.get("price_change_5m"), "15m": price_data.get("price_change_15m")}
            volume_changes = {"1m": volume_1m, "5m": volume_5m, "15m": volume_15m, "1h": volume_1h}

            # Generate signal
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

# Run the monitor every minute
if __name__ == "__main__":
    while True:
        monitor_pairs()
        time.sleep(60)
