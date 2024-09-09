from services.binance_api import get_open_interest_change, get_price_data, get_volume
from services.signal_generation import generate_signal
from services.telegram import send_telegram_message

# Symbols to monitor
SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT']

# Price and volume history
price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}

# Function to monitor pairs and check for signal generation
def monitor_pairs():
    for symbol in SYMBOLS:
        oi_5m = get_open_interest_change(symbol, '5m')
        price_data = get_price_data(symbol)
        current_price = price_data.get("price", None)
        
        # Update price history
        if current_price is not None:
            price_history[symbol].append(current_price)

        # Ensure we have enough data for calculating changes
        if len(price_history[symbol]) >= 2:
            price_change_1m = ((current_price - price_history[symbol][-2]) / price_history[symbol][-2]) * 100
        else:
            price_change_1m = None

        # Additional price change calculations for 5m, 15m, 1h...

        # Fetch volume
        current_volume = get_volume(symbol)
        if current_volume != "N/A":
            volume_history[symbol].append(current_volume)

        # Ensure enough data for volume change calculations
        if len(volume_history[symbol]) >= 2:
            volume_change_1m = ((current_volume - volume_history[symbol][-2]) / volume_history[symbol][-2]) * 100
        else:
            volume_change_1m = None

        # OI, price, and volume changes for the signal generation function
        oi_changes = {"1m": oi_5m}
        price_changes = {"1m": price_change_1m}
        volume_changes = {"1m": volume_change_1m}

        # Generate signal
        signal = generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes)
        
        # Send the signal via Telegram
        if signal:
            send_telegram_message(signal)

# Run the monitor function every minute
while True:
    monitor_pairs()
    time.sleep(60)
