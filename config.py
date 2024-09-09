from collections import deque

SYMBOLS = ['HFTUSDT', 'XVSUSDT', 'LSKUSDT', 'ONGUSDT', 'BNTUSDT', 'BTCDOMUSDT', 'MTLUSDT', 'ORBSUSDT', 'ARKUSDT', 'TIAUSDC', 'ICXUSDT', 'ONEUSDT', 'AGLDUSDT', 'TWTUSDT']

price_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
volume_history = {symbol: deque(maxlen=60) for symbol in SYMBOLS}
rsi_history = {symbol: {interval: deque(maxlen=60) for interval in ["1m", "5m", "15m", "1h", "24h"]} for symbol in SYMBOLS}
