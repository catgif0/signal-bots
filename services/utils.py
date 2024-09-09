import numpy as np

def calculate_rsi(prices, period=14):
    if len(prices) < period:
        return None

    deltas = np.diff(prices)
    seed = deltas[:period]
    up = seed[seed >= 0].sum() / period
    down = -seed[seed < 0].sum() / period

    if down == 0:
        rs = np.inf
    else:
        rs = up / down

    rsi = 100 - (100 / (1 + rs))

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

def calculate_change_with_emoji(change_value):
    if change_value is None:
        return "N/A"
    if change_value > 0:
        return f"🟩{change_value:.3f}%"
    elif change_value < 0:
        return f"🟥{change_value:.3f}%"
    else:
        return "⬜0.000%"
