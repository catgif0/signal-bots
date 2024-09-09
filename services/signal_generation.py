import time
import logging

signal_status = {}  # Dictionary to store signal statuses per symbol

def generate_signal(symbol, current_price, oi_changes, price_changes, volume_changes):
    global signal_status
    
    # Initialize signal status for the symbol if not already present
    if symbol not in signal_status:
        signal_status[symbol] = {
            'step': 0,  # No signal yet
            'last_signal_time': time.time()  # Track time of last signal
        }
    
    # Log the fetched changes for debugging purposes
    logging.debug(f"OI Changes for {symbol}: {oi_changes}")
    logging.debug(f"Price Changes for {symbol}: {price_changes}")
    logging.debug(f"Volume Changes for {symbol}: {volume_changes}")
    
    # Conditions for the initial reversal based on 1-minute data (Step 1)
    oi_condition_1m = oi_changes.get("1m") is not None and oi_changes["1m"] > 1.0
    price_condition_1m = price_changes.get("1m") is not None and price_changes["1m"] > 0.5
    volume_condition_1m = volume_changes.get("1m") is not None and volume_changes["1m"] > 5.0

    # Initial reversal signal (Step 1)
    if signal_status[symbol]['step'] == 0 and (oi_condition_1m or price_condition_1m or volume_condition_1m):
        stop_loss = current_price * 0.98  # 2% below the current price
        risk = current_price - stop_loss
        take_profit = current_price + (2 * risk)

        # Send initial reversal signal based on 1-minute data (Step 1)
        signal_message = (
            f"STEP 1: INITIAL REVERSAL SPOTTED (1m Data)!\n\n"
            f"PAIR: {symbol}\n"
            f"Price: ${current_price:.2f}\n"
            f"Stop Loss: ${stop_loss:.2f}\n"
            f"TP1: ${take_profit:.2f}\n"
            f"TP2: ${take_profit * 1.5:.2f}\n"
            f"TP3: ${take_profit * 2:.2f}\n"
        )

        signal_status[symbol]['step'] = 1  # Move to step 1
        signal_status[symbol]['last_signal_time'] = time.time()  # Update the time of the last signal
        return signal_message
    
    # Step 2: Confirm after 5-15 minutes
    elif signal_status[symbol]['step'] == 1:
        time_since_last_signal = time.time() - signal_status[symbol]['last_signal_time']
        
        # Check if 5 to 15 minutes have passed
        if 5 * 60 <= time_since_last_signal <= 15 * 60:
            # Conditions for continuing reversal in 5-minute data
            oi_condition_5m = oi_changes.get("5m") is not None and oi_changes["5m"] > 1.5
            price_condition_5m = price_changes.get("5m") is not None and price_changes["5m"] > 1.3
            volume_condition_5m = volume_changes.get("5m") is not None and volume_changes["5m"] > 12

            if oi_condition_5m and (price_condition_5m or volume_condition_5m):
                # Send confirmation signal (Step 2)
                signal_message = (
                    f"STEP 2: TREND CONFIRMED AFTER 5-15 MINUTES!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend sustains. Consider re-entry or adjusting positions."
                )
                signal_status[symbol]['step'] = 2  # Move to step 2
                signal_status[symbol]['last_signal_time'] = time.time()  # Update time
                return signal_message
            else:
                # Reset signal tracking if the trend weakens
                signal_message = (
                    f"STEP 2: TREND WEAKENED!\n\n"
                    f"PAIR: {symbol}\n"
                    f"Price: ${current_price:.2f}\n"
                    f"Trend failed to confirm within 5-15 minutes. Reversal invalidated."
                )
                signal_status[symbol]['step'] = 0  # Reset to initial state
                return signal_message

    # Additional steps (Step 3, Step 4) can follow the same pattern as Step 2...

    logging.info(f"No signal generated for {symbol}. Monitoring OI, price, and volume changes.")
    return None
