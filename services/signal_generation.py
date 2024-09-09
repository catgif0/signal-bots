def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    # Check if price_changes has at least 2 elements
    if len(price_changes) >= 2:
        price_change_1m = ((current_price - price_changes[-2]) / price_changes[-2]) * 100
    else:
        # Handle the case where there aren't enough price changes
        price_change_1m = None
        print(f"Error: Not enough price data for {symbol}. Length of price_changes: {len(price_changes)}")
        # You can also log this issue or handle it in another way, such as skipping this pair
        return None

    # Continue with your signal generation logic
    signal = f"Signal for {symbol}: Price change 1m: {price_change_1m}%"
    
    return signal
