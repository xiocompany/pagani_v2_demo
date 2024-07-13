import ccxt
import pandas as pd
from datetime import datetime, timedelta
import time

# Initialize the exchange
exchange = ccxt.bingx()

# Define the symbol and timeframe
symbol = 'BTC/USDT:USDT'
timeframe = '1m'

# Loop to repeat every 60 seconds
while True:
    # Calculate the timestamp for the past 7 days
    now = datetime.utcnow()
    seven_days_ago = now - timedelta(days=7)
    since = exchange.parse8601(seven_days_ago.isoformat())

    # Fetch OHLCV data
    ohlcv = []
    while since < exchange.parse8601(now.isoformat()):
        data = exchange.fetch_ohlcv(symbol, timeframe, since=since)
        if len(data) == 0:
            break
        since = data[-1][0] + 1  # Move the 'since' parameter to the last fetched timestamp
        ohlcv.extend(data)

    # Convert the data to a pandas DataFrame
    data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])

    # Convert timestamp to datetime
    data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

    # Save the data to a CSV file
    csv_file = "BTCUSDT_ohlc_data_1min.csv"
    data.to_csv(csv_file, index=False)

    print(f"Data saved to {csv_file}")

    # Wait for 60 seconds before repeating
    time.sleep(60)
