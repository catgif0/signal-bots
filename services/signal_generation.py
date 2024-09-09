import logging
from services.utils import calculate_rsi

def generate_signal(symbol, current_price, oi_changes, price_history, volume_history, rsi_history):
    logging.debug(f"Generating signal for {symbol}")

    price_change_1m = ((current_price - price_history[-2]) / price_history[-2]) * 100 if len(price_history) >= 2 else None
    volume_change_1m = ((volume_history[-1] - volume_history[-2]) / volume_history[-2]) * 100 if len(volume_history) >= 2 else None
    
    rsi_1m = calculate_rsi(list(price_history), period=14)
    
    # Example signal conditions
    if oi_changes['1m'] > 1 and rsi_1m < 30:
        message = f"Reversal spotted for {symbol}! Price: {current_price:.2f}, OI: {oi_changes['1m']:.2f}, RSI: {rsi_1m:.2f}"
        return message
    
    return None
