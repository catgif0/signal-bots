from services.signal_generation import generate_signal  # Assuming your architecture
from services.telegram import send_telegram_message  # Assuming your architecture
from services.binance_api import get_open_interest_change, get_price_data, get_volume  # Assuming your architecture

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 'ORBSUSDT', 'ARKUSDT', 'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

# Price and volume history to track changes over time intervals
price_history = {
    symbol: deque(maxlen=60) for symbol in SYMBOLS  # Store up to 60 prices (one price per minute)
}
volume_history = {
    symbol: deque(maxlen=60) for symbol in SYMBOLS  # Store up to 60 volume data points (one volume per minute)
}

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    logging.info("Monitoring started for all symbols.")
    for symbol in SYMBOLS:
        try:
            # Fetch OI changes and price changes from your existing logic
            logging.info(f"Fetching OI and price data for {symbol}.")
            oi_5m = get_open_interest_change(symbol, '5m')
            oi_15m = get_open_interest_change(symbol, '15m')
            oi_1h = get_open_interest_change(symbol, '1h')
            oi_24h = get_open_interest_change(symbol, '1d')

            logging.debug(f"OI Data for {symbol}: 5m={oi_5m}, 15m={oi_15m}, 1h={oi_1h}, 1d={oi_24h}")

            price_data = get_price_data(symbol)
            current_price = price_data.get("price", None)

            # Append current price and volume to history
            price_history[symbol].append(current_price)

            # Ensure enough historical data is present in deque before calculating changes
            price_change_1m = ((current_price - price_history[symbol][-2]) / price_history[symbol][-2]) * 100 if len(price_history[symbol]) >= 2 else None
            price_change_5m = ((current_price - price_history[symbol][-5]) / price_history[symbol][-5]) * 100 if len(price_history[symbol]) >= 5 else None
            price_change_15m = ((current_price - price_history[symbol][-15]) / price_history[symbol][-15]) * 100 if len(price_history[symbol]) >= 15 else None
            price_change_1h = ((current_price - price_history[symbol][-60]) / price_history[symbol][-60]) * 100 if len(price_history[symbol]) >= 60 else None
            price_change_24h = price_data.get("price_change_24h", None)

            # Fetch volume changes
            current_volume = get_volume(symbol)
            volume_history[symbol].append(current_volume)
            volume_change_1m = ((current_volume - volume_history[symbol][-2]) / volume_history[symbol][-2]) * 100 if len(volume_history[symbol]) >= 2 else None
            volume_change_5m = ((current_volume - volume_history[symbol][-5]) / volume_history[symbol][-5]) * 100 if len(volume_history[symbol]) >= 5 else None
            volume_change_15m = ((current_volume - volume_history[symbol][-15]) / volume_history[symbol][-15]) * 100 if len(volume_history[symbol]) >= 15 else None
            volume_change_1h = ((current_volume - volume_history[symbol][-60]) / volume_history[symbol][-60]) * 100 if len(volume_history[symbol]) >= 60 else None

            logging.debug(f"Price changes for {symbol}: 1m={price_change_1m}, 5m={price_change_5m}, 15m={price_change_15m}, 1h={price_change_1h}, 24h={price_change_24h}")
            logging.debug(f"Volume changes for {symbol}: 1m={volume_change_1m}, 5m={volume_change_5m}, 15m={volume_change_15m}, 1h={volume_change_1h}")

            # Create dictionaries of OI, price, and volume changes for the symbol
            oi_changes = {"1m": oi_5m, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
            price_changes = {"1m": price_change_1m, "5m": price_change_5m, "15m": price_change_15m, "1h": price_change_1h, "24h": price_change_24h}
            volume_changes = {"1m": volume_change_1m, "5m": volume_change_5m, "15m": volume_change_15m, "1h": volume_change_1h}

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
