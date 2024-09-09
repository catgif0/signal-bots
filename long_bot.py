from services.binance_api import get_open_interest_change, get_price_data, get_volume
from services.telegram import send_telegram_message
from signals.signal_generation import generate_signal
from config import SYMBOLS, price_history, volume_history, rsi_history
from collections import deque
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def monitor_pairs():
    for symbol in SYMBOLS:
        price_data = get_price_data(symbol)
        current_price = price_data.get("price", None)

        if current_price is not None:
            price_history[symbol].append(current_price)

        # Fetching and processing data for OI, price changes, volume, and RSI
        oi_changes = {
            "1m": get_open_interest_change(symbol, '5m'),
            "5m": get_open_interest_change(symbol, '5m'),
            "15m": get_open_interest_change(symbol, '15m'),
            "1h": get_open_interest_change(symbol, '1h'),
            "24h": get_open_interest_change(symbol, '1d')
        }

        current_volume = get_volume(symbol)
        if current_volume is not None:
            volume_history[symbol].append(current_volume)

        signal = generate_signal(symbol, current_price, oi_changes, price_history[symbol], volume_history[symbol], rsi_history[symbol])
        
        if signal:
            send_telegram_message(signal)
