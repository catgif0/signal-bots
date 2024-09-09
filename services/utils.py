import numpy as np

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    rs = up / down if down != 0 else np.inf
    rsi = 100 - (100 / (1 + rs))

    for delta in deltas[period:]:
        upval = delta if delta > 0 else 0
        downval = -delta if delta < 0 else 0
        up = (up * (period - 1) + upval) / period
        down = (down * (period - 1) + downval) / period
        rs = up / down if down != 0 else np.inf
        rsi = 100 - (100 / (1 + rs))

    return rsi
