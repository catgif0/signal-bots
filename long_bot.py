import logging
import time
from services.signal_generation import get_oi_data, get_price_data, get_volume_data
from services.notification import send_signal_notification

def monitor_market():
    symbols = ["HFTUSDT", "XVSUSDT", "LSKUSDT", "ONGUSDT", "BNTUSDT", "BTCDOMUSDT"]  # Add your symbol list here

    while True:
        for symbol in symbols:
            try:
                logging.info(f"Fetching OI, price, and volume data for {symbol}.")
                
                oi_data = get_oi_data(symbol)
                price_data = get_price_data(symbol)
                volume_data = get_volume_data(symbol)

                # Handle None checks before proceeding
                if any(data is None for data in [oi_data, price_data, volume_data]):
                    logging.error(f"Data for {symbol} contains None values, skipping.")
                    continue
                
                logging.info(f"PAIR: {symbol}")
                logging.info(f"Price: {price_data.get('1m', 'N/A')}")
                logging.info(f"OI 1m: {oi_data.get('1m')}, OI 5m: {oi_data.get('5m')}, OI 15m: {oi_data.get('15m')}, OI 1h: {oi_data.get('1h')}, OI 24h: {oi_data.get('24h')}")
                logging.info(f"Volume 1m: {volume_data.get('1m')}, Volume 5m: {volume_data.get('5m')}, Volume 15m: {volume_data.get('15m')}, Volume 1h: {volume_data.get('1h')}")

                signal = calculate_signal(symbol, price_data, oi_data, volume_data)
                if signal:
                    send_signal_notification(signal)

            except Exception as e:
                logging.error(f"Error while processing {symbol}: {e}")

        logging.info("Monitoring completed for this iteration.")
        time.sleep(60)  # Wait for 1 minute before the next iteration

def calculate_signal(pair, price_data, oi_data, volume_data):
    try:
        # Check if 1m data exists and significant
        if oi_data['1m'] is not None and oi_data['1m'] > 0:
            # Check if all other timeframes are negative
            if all(oi <= 0 for oi in [oi_data.get('5m'), oi_data.get('15m'), oi_data.get('1h'), oi_data.get('24h')]):
                # Ensure volume and price change are significant
                if price_data.get('1m') and volume_data.get('1m'):
                    volume_change = (volume_data['1m'] - volume_data['5m']) / volume_data['5m']
                    price_change = (price_data['1m'] - price_data['5m']) / price_data['5m']

                    if volume_change > 0.20 or price_change > 0.01:
                        return generate_signal(pair, price_data, oi_data, volume_data)
    except Exception as e:
        logging.error(f"Error while generating signal for {pair}: {e}")

    return None

def generate_signal(pair, price_data, oi_data, volume_data):
    signal = {
        "pair": pair,
        "price": price_data['1m'],
        "stop_loss": price_data['1m'],
        "tp1": price_data['1m'] * 1.05,  # Example TP values
        "tp2": price_data['1m'] * 1.10,
        "tp3": price_data['1m'] * 1.20,
        "oi_1m": oi_data['1m'],
        "oi_5m": oi_data['5m'],
        "oi_15m": oi_data['15m'],
        "oi_1h": oi_data['1h'],
        "oi_24h": oi_data['24h'],
        "volume_1m": volume_data['1m'],
        "volume_5m": volume_data['5m'],
        # Additional data can be added for more detailed tracking
    }
    logging.info(f"Signal generated for {pair}: {signal}")
    return signal

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    monitor_market()
