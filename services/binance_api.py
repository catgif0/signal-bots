import requests
import logging

# Fetch open interest change for the symbol
def get_open_interest_change(symbol, interval):
    try:
        url = "https://fapi.binance.com/futures/data/openInterestHist"
        params = {"symbol": symbol, "period": interval, "limit": 2}  # We need the last two data points to calculate the change
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

# Fetch the latest funding rate
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
