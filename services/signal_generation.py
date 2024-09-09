def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    # Initialize the variables to None
    price_change_1m = None
    price_change_5m = None
    price_change_15m = None
    price_change_1h = None
    
    # Check if the price_changes list has enough data for each calculation
    if len(price_changes) >= 2:
        price_change_1m = ((current_price - price_changes[-2]) / price_changes[-2]) * 100

    if len(price_changes) >= 5:
        price_change_5m = ((current_price - price_changes[-5]) / price_changes[-5]) * 100

    if len(price_changes) >= 15:
        price_change_15m = ((current_price - price_changes[-15]) / price_changes[-15]) * 100

    if len(price_changes) >= 60:
        price_change_1h = ((current_price - price_changes[-60]) / price_changes[-60]) * 100

    # Similar checks for other variables if needed
    # Generate signal based on available changes
    signal = None
    if price_change_1m or price_change_5m or price_change_15m or price_change_1h:
        signal = f"Signal for {symbol}: Price change 1m: {price_change_1m}%, 5m: {price_change_5m}%, 15m: {price_change_15m}%, 1h: {price_change_1h}%"
    
    return signal
