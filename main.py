import time
from long_bot import monitor_pairs

if __name__ == "__main__":
    while True:
        monitor_pairs()
        time.sleep(60)
