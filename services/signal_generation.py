def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    # Ensure price_changes has at least 2 elements before accessing [-2]
    if len(price_changes) >= 2:
        price_change_1m = ((current_price - price_changes[-2]) / price_changes[-2]) * 100
    else:
        # Handle the case where there are not enough price changes
        price_change_1m = None
        print(f"Warning: Not enough price data for {symbol}. Skipping this calculation.")
        return None

    # Continue your logic for signal generation
    signal = f"Signal for {symbol}: Price change 1m: {price_change_1m}%"
    
    return signal
