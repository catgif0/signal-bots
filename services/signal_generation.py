def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    # Initialize variables
    price_change_1m = None
    
    # Ensure price_changes has enough elements before calculating the changes
    if len(price_changes) >= 2:
        price_change_1m = ((current_price - price_changes[-2]) / price_changes[-2]) * 100
    else:
        # Handle the case where there aren't enough price changes
        price_change_1m = None

    # Continue with your signal generation logic using the safe price_change_1m value
    signal = f"Signal for {symbol}: Price change 1m: {price_change_1m}%"
    
    return signal
