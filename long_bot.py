import time
import requests
import os
import logging
import numpy as np  # Importing NumPy for RSI calculation
from collections import deque
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from threading import Thread

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
price_history = {
    symbol: deque(maxlen=60) for symbol in SYMBOLS  # Store up to 60 prices (one price per minute)
}
volume_history = {
    symbol: deque(maxlen=60) for symbol in SYMBOLS  # Store up to 60 volume data points (one volume per minute)
}
rsi_history = {
    symbol: {
        "1m": deque(maxlen=60),
        "5m": deque(maxlen=60),
        "15m": deque(maxlen=60),
        "1h": deque(maxlen=60),
        "24h": deque(maxlen=60)
    } for symbol in SYMBOLS
}

# Initialize FastAPI app
app = FastAPI()

logging.info("Starting signal_bot.py")

# Function to send a message to Telegram
def send_telegram_message(message):
    try:
        chat_ids = get_chat_ids()
        if not chat_ids:
            logging.error("No chat IDs found where the bot is admin or in private chats.")
            return
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        for chat_id in chat_ids:
            payload = {
                'chat_id': chat_id,
                'text': message,
                'parse_mode': 'HTML'
            }
            response = requests.post(url, data=payload)
            logging.info(f"Sending to Telegram chat {chat_id}: {message}")
            logging.info(f"Telegram response: {response.status_code}, {response.text}")
    except Exception as e:
        logging.error(f"Failed to send Telegram message: {e}")

# Function to get chat IDs from Telegram
def get_chat_ids():
    try:
        logging.info("Fetching updates to identify chat IDs...")
        updates_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        response = requests.get(updates_url)
        if response.status_code != 200:
            logging.error(f"Failed to fetch updates: {response.status_code}, {response.text}")
            return []
        data = response.json()
        chat_ids = set()

        if 'result' in data:
            for update in data['result']:
                if 'message' in update or 'channel_post' in update:
                    chat = update.get('message', update.get('channel_post')).get('chat')
                    chat_id = chat['id']
                    chat_type = chat['type']
                    logging.info(f"Found chat ID: {chat_id} of type {chat_type}. Checking if bot is an admin...")
                    if chat_type == 'private':
                        chat_ids.add(chat_id)
                    else:
                        admin_check_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getChatAdministrators?chat_id={chat_id}"
                        admin_response = requests.get(admin_check_url)
                        admin_data = admin_response.json()
                        if admin_response.status_code == 200 and 'result' in admin_data:
                            for admin in admin_data['result']:
                                if admin['user']['id'] == int(TELEGRAM_BOT_TOKEN.split(':')[0]):
                                    chat_ids.add(chat_id)
        return list(chat_ids)
    except Exception as e:
        logging.error(f"Failed to get chat IDs: {e}")
        return []

# Fetch open interest change for the symbol
def get_open_interest_change(symbol, interval):
    try:
        url = "https://fapi.binance.com/futures/data/openInterestHist"
        params = {
            "symbol": symbol,
            "period": interval,
            "limit": 2  # We need the last two data points to calculate the change
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch open interest: {response.status_code}, {response.text}")
            return None
        data = response.json()
        if len(data) < 2:
            return None
        oi_change = ((float(data[-1]['sumOpenInterest']) - float(data[-2]['sumOpenInterest'])) / float(data[-2]['sumOpenInterest'])) * 100
        return oi_change
    except Exception as e:
        logging.error(f"Failed to fetch open interest change: {e}")
        return None

# Fetch latest price and price change percentage for the symbol
def get_price_data(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch price data: {response.status_code}, {response.text}")
            return {}
        data = response.json()
        price = float(data['lastPrice'])  # Fetch the current price
        price_change_24h = float(data['priceChangePercent'])  # 24-hour price change percentage
        return {
            "price": price,
            "price_change_24h": price_change_24h
        }
    except Exception as e:
        logging.error(f"Failed to fetch price data: {e}")
        return {}

# Fetch 24-hour volume
def get_volume(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch volume: {response.status_code}, {response.text}")
            return "N/A"
        data = response.json()
        volume = float(data['volume'])  # Current cumulative volume for the last 24 hours
        return volume
    except Exception as e:
        logging.error(f"Failed to fetch volume: {e}")
        return "N/A"

# Function to fetch the latest funding rate
def get_funding_rate(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {
            "symbol": symbol,
            "limit": 1
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch funding rate: {response.status_code}, {response.text}")
            return "N/A"
        data = response.json()
        if len(data) > 0:
            funding_rate = float(data[0]["fundingRate"]) * 100
            return f"{funding_rate:.2f}%"
        return "N/A"
    except Exception as e:
        logging.error(f"Failed to fetch funding rate: {e}")
        return "N/A"

# Calculate change percentage with emojis
def calculate_change_with_emoji(change_value):
    if change_value is None:
        return "N/A"
    if change_value > 0:
        return f"🟩{change_value:.3f}%"
    elif change_value < 0:
        return f"🟥{change_value:.3f}%"
    else:
        return "⬜0.000%"

# Function to calculate RSI
def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None  # Not enough data points

    deltas = np.diff(prices)  # Calculate price changes
    seed = deltas[:period]  # Get the first 'period' number of changes
    up = seed[seed >= 0].sum() / period  # Average gain
    down = -seed[seed < 0].sum() / period  # Average loss

    if down == 0:
        rs = np.inf
    else:
        rs = up / down  # Relative strength

    rsi = 100 - (100 / (1 + rs))

    # Now calculate the rest of the RSI values using exponential moving average
    for delta in deltas[period:]:
        if delta > 0:
            upval = delta
            downval = 0
        else:
            upval = 0
            downval = -delta

        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period

        rs = up / down if down != 0 else np.inf
        rsi = 100 - (100 / (1 + rs))

    return rsi

# Dictionary to store signal statuses per symbol
signal_status = {}

def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    global signal_status
    
    # Initialize signal status for the symbol if not already present
    if symbol not in signal_status:
        signal_status[symbol] = {
            'step': 0,  # No signal yet
            'last_signal_time': time.time()  # Track time of last signal
        }
    
    # Log the fetched changes for debugging purposes
    logging.debug(f"OI Changes for {symbol}: {oi_changes}")
    logging.debug(f"Price Changes for {symbol}: {price_changes}")
    logging.debug(f"Volume Changes for {symbol}: {volume_changes}")
    logging.debug(f"RSI Changes for {symbol}: {rsi_changes}")
    
    # Conditions for the initial reversal based on 1-minute data (Step 1)
    oi_condition_1m = oi_changes.get("1m") is not None and oi_changes["1m"] > 1.0
    price_condition_1m = price_changes.get("1m") is not None and price_changes["1m"] > 0.5
    volume_condition_1m = volume_changes.get("1m") is not None and volume_changes["1m"] > 5.0
    rsi_condition_1m = rsi_changes.get("1m") is not None and rsi_changes["1m"] < 30  # Example RSI condition for oversold

    # Initial reversal signal (Step 1)
    if signal_status[symbol]['step'] == 0 and (oi_condition_1m or price_condition_1m or volume_condition_1m or rsi_condition_1m):
        stop_loss = current_price * 0.98  # 2% below the current price
        risk = current_price - stop_loss
        take_profit = current_price + (2 * risk)

        # Send initial reversal signal based on 1-minute data (Step 1)
        signal_message = (
            f"STEP 1: INITIAL REVERSAL SPOTTED (1m Data)!\n\n"
            f"PAIR: {symbol}\n"
            f"Price: ${current_price:.2f}\n"
            f"Stop Loss: ${stop_loss:.2f}\n"
            f"TP1: ${take_profit:.2f}\n"
            f"TP2: ${take_profit * 1.5:.2f}\n"
            f"TP3: ${take_profit * 2:.2f}\n"
        )

        signal_status[symbol]['step'] = 1  # Move to step 1
        signal_status[symbol]['last_signal_time'] = time.time()  # Update the time of the last signal
        return signal_message
    
    # Step 2: Confirm after 5-15 minutes
    elif signal_status[symbol]['step'] == 1:
        time_since_last_signal = time.time() - signal_status[symbol]['last_signal_time']
        
        # Check if 5 to 15 minutes have passed
        if 5 * 60 <= time_since_last_signal <= 15 * 60:
            # Conditions for continuing reversal in 5-minute data
            oi_condition_5m = oi_changes.get("5m") is not None and oi_changes["5m"] > 1.5
            price_condition_5m = price_changes.get("5m") is not None and price_changes["5m"] > 1.3
            volume_condition_5m = volume_changes.get("5m") is not None and volume_changes["5m"] > 12
            rsi_condition_5m = rsi_changes.get("5m") is not None and rsi_changes["5m"] < 30  # Example RSI condition

            if oi_condition_5m and (price_condition_5m or volume_condition_5m or rsi_condition_5m):
                # Send confirmation signal (Step 2)
                signal_message = (
                    f"STEP 2: TREND CONFIRMED AFTER 5-15 MINUTES!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend sustains. Consider re-entry or adjusting positions."
                )
                signal_status[symbol]['step'] = 2  # Move to step 2
                signal_status[symbol]['last_signal_time'] = time.time()  # Update time
                return signal_message
            else:
                # Reset signal tracking if the trend weakens
                signal_message = (
                    f"STEP 2: TREND WEAKENED!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend failed to confirm within 5-15 minutes. Reversal invalidated."
                )
                signal_status[symbol]['step'] = 0  # Reset to initial state
                return signal_message

    # Step 3: Confirm after 15-60 minutes
    elif signal_status[symbol]['step'] == 2:
        time_since_last_signal = time.time() - signal_status[symbol]['last_signal_time']
        
        # Check if 15 to 60 minutes have passed
        if 15 * 60 <= time_since_last_signal <= 60 * 60:
            # Conditions for sustained trend in 15-minute data
            oi_condition_15m = oi_changes.get("15m") is not None and oi_changes["15m"] > 1.5
            price_condition_15m = price_changes.get("15m") is not None and price_changes["15m"] > 1.3
            volume_condition_15m = volume_changes.get("15m") is not None and volume_changes["15m"] > 12
            rsi_condition_15m = rsi_changes.get("15m") is not None and rsi_changes["15m"] < 30  # Example RSI condition

            if oi_condition_15m and (price_condition_15m or volume_condition_15m or rsi_condition_15m):
                # Send confirmation signal (Step 3)
                signal_message = (
                    f"STEP 3: TREND CONFIRMED AFTER 15-60 MINUTES!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend continues. Strong signals of a lasting reversal."
                )
                signal_status[symbol]['step'] = 3  # Move to step 3
                signal_status[symbol]['last_signal_time'] = time.time()  # Update time
                return signal_message
            else:
                # Reset signal tracking if the trend weakens
                signal_message = (
                    f"STEP 3: TREND WEAKENED!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend failed to confirm within 15-60 minutes. Signal cancelled."
                )
                signal_status[symbol]['step'] = 0  # Reset to initial state
                return signal_message

    # Step 4: Confirm after 1 hour
    elif signal_status[symbol]['step'] == 3:
        time_since_last_signal = time.time() - signal_status[symbol]['last_signal_time']
        
        # Check if 1 hour has passed
        if time_since_last_signal >= 60 * 60:
            # Conditions for sustained trend in 1-hour timeframe
            oi_condition_1h = oi_changes.get("1h") is not None and oi_changes["1h"] > 1.5
            price_condition_1h = price_changes.get("1h") is not None and price_changes["1h"] > 1.3
            volume_condition_1h = volume_changes.get("1h") is not None and volume_changes["1h"] > 12
            rsi_condition_1h = rsi_changes.get("1h") is not None and rsi_changes["1h"] < 30  # Example RSI condition

            if oi_condition_1h and (price_condition_1h or volume_condition_1h or rsi_condition_1h):
                # Send final confirmation signal (Step 4)
                signal_message = (
                    f"STEP 4: TREND SUSTAINED FOR 1 HOUR!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"The reversal has held for 1 hour. Strong trend continuation likely."
                )
                signal_status[symbol]['step'] = 4  # Move to step 4 (final step)
                return signal_message
            else:
                # Reset signal tracking if the trend weakens
                signal_message = (
                    f"STEP 4: TREND FAILED TO SUSTAIN!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Reversal did not hold for 1 hour. Signal cancelled."
                )
                signal_status[symbol]['step'] = 0  # Reset to initial state
                return signal_message
    
    # No signal generated at this point
    logging.info(f"No signal generated for {symbol}. Monitoring OI, price, volume, and RSI changes.")
    return None


# Function to monitor pairs and check for signal generation
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
