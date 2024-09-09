import time
import time
import requests
import os
import logging
from collections import deque 
from long_bot import monitor_pairs

if __name__ == "__main__":
    while True:
        monitor_pairs()
        time.sleep(60)
