import requests
import logging

def get_open_interest_change(symbol, interval):
    try:
        url = "https://fapi.binance.com/futures/data/openInterestHist"
        params = {"symbol": symbol, "period": interval, "limit": 2}
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

def get_price_data(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch price data: {response.status_code}, {response.text}")
            return {}
        data = response.json()
        price = float(data['lastPrice'])
        price_change_24h = float(data['priceChangePercent'])
        return {"price": price, "price_change_24h": price_change_24h}
    except Exception as e:
        logging.error(f"Failed to fetch price data: {e}")
        return {}

def get_volume(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
        params = {"symbol": symbol}
        response = requests.get(url, params=params)
        if response.status_code != 200:
            logging.error(f"Failed to fetch volume: {response.status_code}, {response.text}")
            return "N/A"
        data = response.json()
        volume = float(data['volume'])
        return volume
    except Exception as e:
        logging.error(f"Failed to fetch volume: {e}")
        return "N/A"

# Add the get_funding_rate function
def get_funding_rate(symbol):
    try:
        url = "https://fapi.binance.com/fapi/v1/fundingRate"
        params = {"symbol": symbol, "limit": 1}
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
