def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes, rsi_changes):
    # Check if there is enough historical data to calculate changes
    price_change_1m = ((current_price - price_changes[-2]) / price_changes[-2]) * 100 if len(price_changes) >= 2 else None
    price_change_5m = ((current_price - price_changes[-5]) / price_changes[-5]) * 100 if len(price_changes) >= 5 else None
    price_change_15m = ((current_price - price_changes[-15]) / price_changes[-15]) * 100 if len(price_changes) >= 15 else None
    price_change_1h = ((current_price - price_changes[-60]) / price_changes[-60]) * 100 if len(price_changes) >= 60 else None

    # Similar handling for volume history
    volume_change_1m = ((current_volume - volume_changes[-2]) / volume_changes[-2]) * 100 if len(volume_changes) >= 2 else None
    volume_change_5m = ((current_volume - volume_changes[-5]) / volume_changes[-5]) * 100 if len(volume_changes) >= 5 else None
    volume_change_15m = ((current_volume - volume_changes[-15]) / volume_changes[-15]) * 100 if len(volume_changes) >= 15 else None
    volume_change_1h = ((current_volume - volume_changes[-60]) / volume_changes[-60]) * 100 if len(volume_changes) >= 60 else None

    # Ensure your calculations only run if there is enough data.
    # Generate signal based on calculated values
    signal = None
    if price_change_1m or price_change_5m or price_change_15m or price_change_1h:
        signal = f"Signal for {symbol}: Price change 1m: {price_change_1m}%, 5m: {price_change_5m}%, 15m: {price_change_15m}%, 1h: {price_change_1h}%"

    return signal
