import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Thresholds for signal generation
THRESHOLDS = {
    'OI': {'step1': 1.0, 'step2': 1.5, 'step3': 1.5, 'step4': 1.5},
    'Price': {'step1': 0.5, 'step2': 1.3, 'step3': 1.3, 'step4': 1.3},
    'Volume': {'step1': 5.0, 'step2': 12.0, 'step3': 12.0, 'step4': 12.0}
}

# Take-profit and stop-loss calculations
def calculate_take_profit(current_price, reward_ratio=2):
    return [
        current_price + current_price * 0.02 * i for i in range(1, 4)
    ]

def calculate_stop_loss(current_price):
    return current_price * 0.98

# Signal generation logic
def generate_signal(pair, current_price, oi_changes, price_changes, volume_changes):
    # Generate signal based on thresholds
    for step in range(1, 5):
        if (oi_changes[f'{step}m'] > THRESHOLDS['OI'][f'step{step}'] and
            price_changes[f'{step}m'] > THRESHOLDS['Price'][f'step{step}'] and
            volume_changes[f'{step}m'] > THRESHOLDS['Volume'][f'step{step}']):
            
            stop_loss = calculate_stop_loss(current_price)
            take_profit = calculate_take_profit(current_price)

            logging.info(f"STEP {step}: Signal Spotted!\nPAIR: {pair}\nPrice: ${current_price:.2f}\nStop Loss: ${stop_loss:.2f}\nTP1: ${take_profit[0]:.2f}, TP2: ${take_profit[1]:.2f}, TP3: ${take_profit[2]:.2f}")
            return {
                'pair': pair,
                'price': current_price,
                'stop_loss': stop_loss,
                'take_profit': take_profit,
                'step': step
            }

    return None
