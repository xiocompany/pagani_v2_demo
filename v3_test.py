import ccxt
import pandas as pd
import joblib
import numpy as np
import time
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
from scipy.spatial.distance import pdist
from scipy import stats

# Load model and scalers
scaler_X = joblib.load('scaler_X.pkl')
scaler_y = joblib.load('scaler_y.pkl')
model = load_model('BILSTM_model.h5')

# Define new functions for feature calculations
def hadamard_transform(prices, period):
    def hadamard_matrix(n):
        if n == 1:
            return np.array([[1]])
        else:
            H = hadamard_matrix(n // 2)
            return np.block([[H, H], [H, -H]]) / np.sqrt(2)

    if len(prices) >= period:
        if (period & (period - 1)) == 0:
            subset = prices[-period:]
            H = hadamard_matrix(len(subset))
            transformed = np.dot(H, subset)
            return transformed
        else:
            return np.zeros(period)
    else:
        return np.zeros(period)

def calculate_brownian_motion(data, N):
    return data['Close'].diff().rolling(window=N).std()

def calculate_entropy(data, N):
    def _entropy(x):
        p_data = pd.Series(x).value_counts() / len(x)
        return stats.entropy(p_data)

    return data['Close'].rolling(window=N).apply(_entropy).fillna(0)

def calculate_fractal_dimension(data, N):
    def _fractal_dimension(x):
        if len(x) < 2:
            return 0
        distances = pdist(np.vstack([np.arange(len(x)), x]).T)
        return stats.linregress(np.log(np.arange(1, len(distances) + 1)), np.log(np.sort(distances)))[0]

    return data['Close'].rolling(window=N).apply(_fractal_dimension).fillna(0)

def calculate_hl_N(data, N):
    high = data['High'].rolling(window=N).max()
    low = data['Low'].rolling(window=N).min()
    return ((high - low) / low) * 100

def calculate_p_N(data, N):
    return ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100

def create_sequences(data, look_back):
    sequences = []
    for i in range(len(data) - look_back):
        sequence = data[i:i + look_back]
        sequences.append(sequence)
    return np.array(sequences)

def predict_new_data(model, scaler_X, scaler_y, data, look_back=90):
    quantum_periods = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    periods = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

    new_features = {}
    for period in quantum_periods:
        new_features[f'Quantum_Feature_{period}'] = data['Close'].rolling(window=period).apply(
            lambda x: hadamard_transform(x, period)[-1] if len(x) == period else np.nan).fillna(0)

    for period in periods:
        new_features[f'Brownian_Motion_{period}'] = calculate_brownian_motion(data, period)
        new_features[f'Entropy_{period}'] = calculate_entropy(data, period)
        new_features[f'Fractal_Dimension_{period}'] = calculate_fractal_dimension(data, period)
        new_features[f'HL_N_{period}'] = calculate_hl_N(data, period)
        new_features[f'P_N_{period}'] = calculate_p_N(data, period)

    new_features_df = pd.DataFrame(new_features)
    data = pd.concat([data.reset_index(drop=True), new_features_df], axis=1).dropna()

    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    features = [col for col in numeric_cols if not col.startswith('T_')]
    X_new = data[features].values

    X_new_scaled = scaler_X.transform(X_new)
    X_new_sequences = create_sequences(X_new_scaled, look_back)

    predictions = pd.DataFrame(index=data.index[-len(X_new_sequences):])
    y_pred_scaled = model.predict(X_new_sequences)
    y_pred = scaler_y.inverse_transform(y_pred_scaled)

    predictions_dict = {f'T_{target}': y_pred[:, i] for i, target in enumerate(range(1, 91))}
    predictions = pd.concat([predictions, pd.DataFrame(predictions_dict)], axis=1)

    return predictions

def main():
    exchange = ccxt.bingx()
    symbol = 'BTC/USDT:USDT'
    timeframe = '1m'

    while True:
        try:
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=1)
            since = exchange.parse8601(seven_days_ago.isoformat())

            ohlcv = []
            while since < exchange.parse8601(now.isoformat()):
                data = exchange.fetch_ohlcv(symbol, timeframe, since=since)
                if len(data) == 0:
                    break
                since = data[-1][0] + 1
                ohlcv.extend(data)

            data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

            data = data[['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume']]
            predictions = predict_new_data(model, scaler_X, scaler_y, data, look_back=90)

            # Print the last row of predictions in a readable format
            last_prediction = predictions[[f'T_{i}' for i in range(1, 91)]].iloc[-1]
            print(last_prediction.to_dict())
            print(f"Datetime in last row: {data['timestamp'].iloc[-1]}")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(10)

if __name__ == "__main__":
    main()
