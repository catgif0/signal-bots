import requests
import logging

# Fetch open interest change for the symbol
def get_open_interest_change(symbol, interval):
    try:
        url = "https://fapi.binance.com/futures/data/openInterestHist"
        params = {
            "symbol": symbol,
            "period": interval,
            "limit": 2
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch open interest: {response.status_code}, {response.text}")
            return None
        data = response.json()
        if len(data) < 2:
            return None
        return ((float(data[-1]['sumOpenInterest']) - float(data[-2]['sumOpenInterest'])) / float(data[-2]['sumOpenInterest'])) * 100
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
        return {"price": float(data['lastPrice']), "price_change_24h": float(data['priceChangePercent'])}
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
            return None
        return float(response.json()['volume'])
    except Exception as e:
        logging.error(f"Failed to fetch volume: {e}")
        return None
