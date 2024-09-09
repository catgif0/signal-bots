import time
import requests
import os
import logging
import numpy as np  # Importing NumPy for RSI calculation
from collections import deque
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from threading import Thread

# Corrected import paths
from services.signal_generation import generate_signal
from services.telegram import send_telegram_message
from services.binance_api import get_open_interest_change, get_price_data, get_volume, get_funding_rate
from services.utils import calculate_rsi, calculate_change_with_emoji

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Telegram Bot token from environment variable
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not TELEGRAM_BOT_TOKEN:
    logging.error("TELEGRAM_BOT_TOKEN environment variable not set")
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 'ORBSUSDT', 'ARKUSDT', 'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

# Price, volume, and RSI history to track changes over time intervals
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
rsi_history = {symbol: {"1m": deque(maxlen=60), "5m": deque(maxlen=60), "15m": deque(maxlen=60), "1h": deque(maxlen=60), "24h": deque(maxlen=60)} for symbol in SYMBOLS}

# Initialize FastAPI app
app = FastAPI()

logging.info("Starting signal_bot.py")

# Dictionary to store signal statuses per symbol
signal_status = {}

def monitor_pairs():
    for symbol in SYMBOLS:
        # Fetch OI changes and price changes from your existing logic
        oi_5m = get_open_interest_change(symbol, '5m')
        oi_15m = get_open_interest_change(symbol, '15m')
        oi_1h = get_open_interest_change(symbol, '1h')
        oi_24h = get_open_interest_change(symbol, '1d')
        
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

        # Calculate RSI for 1m, 5m, 15m, 1h, and 24h based on price history
        rsi_1m = calculate_rsi(list(price_history[symbol])[-2:], period=14) if len(price_history[symbol]) >= 2 else None
        rsi_5m = calculate_rsi(list(price_history[symbol])[-5:], period=14) if len(price_history[symbol]) >= 5 else None
        rsi_15m = calculate_rsi(list(price_history[symbol])[-15:], period=14) if len(price_history[symbol]) >= 15 else None
        rsi_1h = calculate_rsi(list(price_history[symbol])[-60:], period=14) if len(price_history[symbol]) >= 60 else None
        rsi_24h = price_data.get('price_change_24h', None)  # Placeholder as you need continuous data for 24h

        # Append the RSI values to rsi_history deques
        rsi_history[symbol]['1m'].append(rsi_1m)
        rsi_history[symbol]['5m'].append(rsi_5m)
        rsi_history[symbol]['15m'].append(rsi_15m)
        rsi_history[symbol]['1h'].append(rsi_1h)
        rsi_history[symbol]['24h'].append(rsi_24h)

        # Create dictionaries of OI, price, volume, and RSI changes for the symbol
        oi_changes = {"1m": oi_5m, "5m": oi_5m, "15m": oi_15m, "1h": oi_1h, "24h": oi_24h}
        price_changes = {"1m": price_change_1m, "5m": price_change_5m, "15m": price_change_15m, "1h": price_change_1h, "24h": price_change_24h}
        volume_changes = {"1m": volume_change_1m, "5m": volume_change_5m, "15m": volume_change_15m, "1h": volume_change_1h}
        rsi_changes = {"1m": rsi_1m, "5m": rsi_5m, "15m": rsi_15m, "1h": rsi_1h, "24h": rsi_24h}

        # Check if conditions for signal generation are met
        signal = generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes)
        
        # If a signal is generated, send it via Telegram
        if signal:
            send_telegram_message(signal)


# Call the monitor_pairs function every minute
while True:
    monitor_pairs()
    time.sleep(60)
