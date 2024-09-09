import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Example thresholds for signal generation
THRESHOLDS = {
    'OI': {'step1': 1.0, 'step2': 1.5, 'step3': 1.5, 'step4': 1.5},
    'Price': {'step1': 0.5, 'step2': 1.3, 'step3': 1.3, 'step4': 1.3},
    'Volume': {'step1': 5.0, 'step2': 12.0, 'step3': 12.0, 'step4': 12.0}
}

# Calculate take-profit and stop-loss
def calculate_take_profit(current_price, reward_ratio=2):
    return [current_price + current_price * 0.02 * i for i in range(1, 4)]

def calculate_stop_loss(current_price):
    return current_price * 0.98

# Helper function to safely compare values, ignoring None values
def safe_compare(value, threshold):
    if value is None:
        return False
    return value > threshold

# Signal generation logic
def generate_signal(pair, current_price, oi_changes, price_changes, volume_changes):
    if (safe_compare(oi_changes['1m'], THRESHOLDS['OI']['step1']) and
        safe_compare(price_changes['1m'], THRESHOLDS['Price']['step1']) and
        safe_compare(volume_changes['1m'], THRESHOLDS['Volume']['step1'])):
        
        stop_loss = calculate_stop_loss(current_price)
        take_profit = calculate_take_profit(current_price)
        logging.info(f"STEP 1: INITIAL REVERSAL SPOTTED (1m Data)!\nPAIR: {pair}\nPrice: ${current_price:.2f}\nStop Loss: ${stop_loss:.2f}\nTP1: ${take_profit[0]:.2f}, TP2: ${take_profit[1]:.2f}, TP3: ${take_profit[2]:.2f}")
        return True

    elif (safe_compare(oi_changes['5m'], THRESHOLDS['OI']['step2']) and
          safe_compare(price_changes['5m'], THRESHOLDS['Price']['step2']) and
          safe_compare(volume_changes['5m'], THRESHOLDS['Volume']['step2'])):
        
        logging.info(f"STEP 2: TREND CONFIRMED AFTER 5-15 MINUTES!\nPAIR: {pair}\nPrice: ${current_price:.2f}\nTrend sustains. Consider re-entry or adjusting positions.")
        return True

    elif (safe_compare(oi_changes['15m'], THRESHOLDS['OI']['step3']) and
          safe_compare(price_changes['15m'], THRESHOLDS['Price']['step3']) and
          safe_compare(volume_changes['15m'], THRESHOLDS['Volume']['step3'])):
        
        logging.info(f"STEP 3: TREND CONFIRMED AFTER 15-60 MINUTES!\nPAIR: {pair}\nPrice: ${current_price:.2f}\nTrend continues. Strong signals of a lasting reversal.")
        return True

    elif (safe_compare(oi_changes['1h'], THRESHOLDS['OI']['step4']) and
          safe_compare(price_changes['1h'], THRESHOLDS['Price']['step4']) and
          safe_compare(volume_changes['1h'], THRESHOLDS['Volume']['step4'])):
        
        logging.info(f"STEP 4: TREND SUSTAINED FOR 1 HOUR!\nPAIR: {pair}\nPrice: ${current_price:.2f}")
        return True

    else:
        return False
