import ccxt
import pandas as pd
import joblib
import numpy as np
import time
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model

# Define trading fee (for example 0.1% fee per trade)
TRADING_FEE = 0.002

# Load model and scalers
scaler_X = joblib.load('scaler_X.pkl')
scaler_y = joblib.load('scaler_y.pkl')
model = load_model('BILSTM_model.h5')

# Initialize trading variables
position = None  # None means no position, otherwise it will be a dict with 'amount', 'entry_price', 'type', and 'leverage'
trades = []

# Define functions as per your provided code
def calculate_fft(data, N):
    close_fft = np.fft.fft(np.asarray(data['Close'].tolist()))
    fft_df = pd.DataFrame({'fft': close_fft})
    fft_df['fft_real'] = fft_df['fft'].apply(lambda x: np.real(x))
    fft_df['fft_imag'] = fft_df['fft'].apply(lambda x: np.imag(x))
    fft_df = fft_df[['fft_real', 'fft_imag']]
    fft_df.columns = [f'fft_{N}_real', f'fft_{N}_imag']
    return fft_df

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

def predict_new_data(model, scaler_X, scaler_y, data, look_back=10):
    periods = [1, 2, 3, 5, 10, 20, 30, 40, 60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900,
               960, 1020, 1080, 1140, 1200, 1260, 1320, 1380, 1440]

    new_features = {}
    for N in periods:
        fft_features = calculate_fft(data, N)
        new_features[f'fft_{N}_real'] = fft_features[f'fft_{N}_real']
        new_features[f'fft_{N}_imag'] = fft_features[f'fft_{N}_imag']
        new_features[f'hl_{N}'] = calculate_hl_N(data, N)
        new_features[f'p_{N}'] = calculate_p_N(data, N)

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

    predictions_dict = {f'T_{target}': y_pred[:, i] for i, target in enumerate(range(1, 121))}
    predictions = pd.concat([predictions, pd.DataFrame(predictions_dict)], axis=1)

    return predictions

# Define trading strategy with leverage and R/R adjustment
def calculate_leverage(target):
    return max(15, min(100, 15 + (100 - 15) * (120 - target) / 119))

def calculate_risk_reward(prediction, threshold=0.4):
    reward = abs(prediction - threshold)
    risk = threshold
    return reward / risk

# Define function to check for emergency conditions based on R/R
def is_emergency_condition_rr(risk_reward, threshold=10):
    return risk_reward > threshold

def trading_strategy(data, predictions):
    global position, trades
    current_price = data['Close'].iloc[-1]
    summary = []  # Summary to collect predictions and actions
    num_positive_predictions = (predictions > 0.4).sum().sum()
    num_negative_predictions = (predictions < -0.4).sum().sum()
    total_predictions = predictions.shape[1]

    for i in range(1, 121):
        prediction = predictions[f'T_{i}'].iloc[-1]
        leverage = calculate_leverage(i)
        risk_reward = calculate_risk_reward(prediction)

        summary.append(f"T_{i}: {prediction:.4f}, Leverage: {leverage}, R/R: {risk_reward:.4f}")

        if position is None:
            if prediction > 0.4 and num_positive_predictions / total_predictions >= 0.9:
                # Check for previous negative predictions
                prev_negatives = any(predictions[f'T_{j}'].iloc[-1] < 0 for j in range(1, i))
                if prev_negatives and not is_emergency_condition_rr(risk_reward):
                    continue  # Wait until a negative prediction before buying
                position = {
                    'type': 'buy',
                    'amount': leverage * risk_reward,
                    'entry_price': current_price,
                    'leverage': leverage,
                    'risk_reward': risk_reward
                }
                trades.append({
                    'action': 'buy',
                    'price': current_price,
                    'amount': leverage * risk_reward,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'time': data['timestamp'].iloc[-1]
                })
                summary.append(f"Buying at {current_price} with leverage {leverage} and R/R {risk_reward} based on T_{i} prediction of {prediction}")
                break
            elif prediction < -0.4 and num_negative_predictions / total_predictions >= 0.9:
                # Check for previous positive predictions
                prev_positives = any(predictions[f'T_{j}'].iloc[-1] > 0 for j in range(1, i))
                if prev_positives and not is_emergency_condition_rr(risk_reward):
                    continue  # Wait until a positive prediction before selling
                position = {
                    'type': 'sell',
                    'amount': leverage * risk_reward,
                    'entry_price': current_price,
                    'leverage': leverage,
                    'risk_reward': risk_reward
                }
                trades.append({
                    'action': 'sell',
                    'price': current_price,
                    'amount': leverage * risk_reward,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'time': data['timestamp'].iloc[-1]
                })
                summary.append(f"Selling at {current_price} with leverage {leverage} and R/R {risk_reward} based on T_{i} prediction of {prediction}")
                break
        else:
            if position['type'] == 'buy':
                # Close buy position (sell to close)
                if prediction < -0.4 or is_emergency_condition_rr(risk_reward):
                    trades.append({
                        'action': 'close_buy',
                        'price': current_price,
                        'amount': position['amount'],
                        'leverage': position['leverage'],
                        'risk_reward': position['risk_reward'],
                        'time': data['timestamp'].iloc[-1]
                    })
                    summary.append(f"Closing buy at {current_price} with R/R {position['risk_reward']} based on T_{i} prediction of {prediction}")
                    position = None
                    break
            elif position['type'] == 'sell':
                # Close sell position (buy to close)
                if prediction > 0.4 or is_emergency_condition_rr(risk_reward):
                    trades.append({
                        'action': 'close_sell',
                        'price': current_price,
                        'amount': position['amount'],
                        'leverage': position['leverage'],
                        'risk_reward': position['risk_reward'],
                        'time': data['timestamp'].iloc[-1]
                    })
                    summary.append(f"Closing sell at {current_price} with R/R {position['risk_reward']} based on T_{i} prediction of {prediction}")
                    position = None
                    break

    print("\n".join(summary))  # Print the summary

# Main loop to fetch data, make predictions, and execute strategy
def main():
    global position, trades
    exchange = ccxt.bingx()
    symbol = 'BTC/USDT:USDT'
    timeframe = '1m'

    while True:
        try:
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)
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
            predictions = predict_new_data(model, scaler_X, scaler_y, data, look_back=60)

            trading_strategy(data, predictions)

            print(f"Datetime in last row: {data['timestamp'].iloc[-1]}")
            print(f"Current position: {position}")
            print(f"Trades: {trades}")

        except Exception as e:
            print(f"An error occurred: {e}")

        time.sleep(25)


if __name__ == "__main__":
    main()
