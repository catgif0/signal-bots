import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Example thresholds for signal generation
THRESHOLDS = {
    'OI': {'1m': 1.0},  # OI change threshold for 1m
    'Price': {'1m': 1.0},  # Price change threshold for 1m
    'Volume': {'1m': 20.0}  # Volume change threshold for 1m (20% increase)
}

# Example take-profit and stop-loss calculations
def calculate_take_profit(current_price, reward_ratio=2):
    return [current_price + current_price * 0.02 * i for i in range(1, 4)]

def calculate_stop_loss(current_price):
    return current_price * 0.98

# Signal generation logic
def generate_signal(pair, current_price, oi_changes, price_changes, volume_changes):
    """
    Signal generation logic based on the OI, price, and volume changes.
    
    Args:
    pair: str: The pair being analyzed (e.g., BTCUSDT)
    current_price: float: The current price of the asset
    oi_changes: dict: Dictionary containing OI changes for different timeframes (1m, 5m, 15m, 1h, 24h)
    price_changes: dict: Dictionary containing price changes for different timeframes
    volume_changes: dict: Dictionary containing volume changes for different timeframes
    
    Returns:
    bool: True if signal is generated, False otherwise
    """
    
    # Condition 1: 1m OI change must be positive and above the threshold
    if oi_changes['1m'] is not None and oi_changes['1m'] > THRESHOLDS['OI']['1m']:
        
        # Condition 2: All other OI changes (5m, 15m, 1h, 24h) must be negative
        if all(oi_changes.get(tf, 0) < 0 for tf in ['5m', '15m', '1h', '24h']):
            
            # Condition 3: Price change must be more than 1% in the last minute
            if price_changes['1m'] is not None and price_changes['1m'] > THRESHOLDS['Price']['1m']:
                
                # Condition 4: Volume change must be more than 20% in the last minute
                if volume_changes['1m'] is not None and volume_changes['1m'] > THRESHOLDS['Volume']['1m']:
                    
                    # Generate signal
                    stop_loss = calculate_stop_loss(current_price)
                    take_profit = calculate_take_profit(current_price)
                    
                    signal_message = (
                        f"STEP 1: INITIAL REVERSAL SPOTTED (1m Data)!\n\n"
                        f"PAIR: {pair}\n"
                        f"Price: ${current_price:.4f}\n"
                        f"Stop Loss: ${stop_loss:.4f}\n"
                        f"TP1: ${take_profit[0]:.4f}, TP2: ${take_profit[1]:.4f}, TP3: ${take_profit[2]:.4f}\n\n"
                        f"🔴 #{pair} ${current_price:.4f} | OI changed in 1m\n\n"
                        f"┌ 🌐 Open Interest \n"
                        f"├ 🟩{oi_changes['1m']:.4f}% (1m)\n"
                        f"├ 🟥{oi_changes['5m']:.4f}% (5m)\n"
                        f"├ 🟥{oi_changes['15m']:.4f}% (15m)\n"
                        f"├ 🟥{oi_changes['1h']:.4f}% (1h)\n"
                        f"└ 🟥{oi_changes['24h']:.4f}% (24h)\n\n"
                        f"┌ 📈 Price change \n"
                        f"├ 🟩{price_changes['1m']:.4f}% (1m)\n"
                        f"└ Volume change 🟩{volume_changes['1m']:.4f}% (1m)"
                    )
                    
                    logging.info(f"Signal Generated: {signal_message}")
                    return signal_message
                
    logging.info(f"No signal generated for {pair}.")
    return False
