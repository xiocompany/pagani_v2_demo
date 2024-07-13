import ccxt
import pandas as pd
import joblib
import numpy as np
import time
from datetime import datetime, timedelta
from tensorflow.keras.models import load_model
import logging
from typing import Dict, List, Optional
import talib

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
TRADING_FEE = 0.002
SYMBOL = 'BTC/USDT:USDT'
TIMEFRAME = '1m'
LOOK_BACK = 60
MODEL_PATH = 'BILSTM_model.h5'
SCALER_X_PATH = 'scaler_X.pkl'
SCALER_Y_PATH = 'scaler_y.pkl'
RISK_PER_TRADE = 0.01  # 1% risk per trade
MOVING_AVERAGE_PERIOD = 200
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# Load model and scalers
scaler_X = joblib.load(SCALER_X_PATH)
scaler_y = joblib.load(SCALER_Y_PATH)
model = load_model(MODEL_PATH)

# Initialize trading variables
position: Optional[Dict] = None
trades: List[Dict] = []

def calculate_fft(data: pd.DataFrame, N: int) -> pd.DataFrame:
    close_fft = np.fft.fft(np.asarray(data['Close'].tolist()))
    fft_df = pd.DataFrame({'fft': close_fft})
    fft_df['fft_real'] = fft_df['fft'].apply(lambda x: np.real(x))
    fft_df['fft_imag'] = fft_df['fft'].apply(lambda x: np.imag(x))
    return fft_df[['fft_real', 'fft_imag']].rename(columns={
        'fft_real': f'fft_{N}_real',
        'fft_imag': f'fft_{N}_imag'
    })

def calculate_hl_N(data: pd.DataFrame, N: int) -> pd.Series:
    high = data['High'].rolling(window=N).max()
    low = data['Low'].rolling(window=N).min()
    return ((high - low) / low) * 100

def calculate_p_N(data: pd.DataFrame, N: int) -> pd.Series:
    return ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100

def create_sequences(data: np.ndarray, look_back: int) -> np.ndarray:
    return np.array([data[i:i + look_back] for i in range(len(data) - look_back + 1)])

def predict_new_data(model, scaler_X, scaler_y, data: pd.DataFrame, look_back: int = LOOK_BACK) -> pd.DataFrame:
    periods = [1, 2, 3, 5, 10, 20, 30, 60, 90, 120, 180, 360, 720]

    new_features = pd.concat([
        calculate_fft(data, N),
        pd.DataFrame({
            f'hl_{N}': calculate_hl_N(data, N),
            f'p_{N}': calculate_p_N(data, N)
        }) for N in periods
    ], axis=1)

    data_with_features = pd.concat([data.reset_index(drop=True), new_features], axis=1).dropna()

    numeric_cols = data_with_features.select_dtypes(include=[np.number]).columns
    features = [col for col in numeric_cols if not col.startswith('T_')]
    X_new = data_with_features[features].values

    X_new_scaled = scaler_X.transform(X_new)
    X_new_sequences = create_sequences(X_new_scaled, look_back)

    y_pred_scaled = model.predict(X_new_sequences)
    y_pred = scaler_y.inverse_transform(y_pred_scaled)

    predictions = pd.DataFrame(
        {f'T_{target}': y_pred[:, i] for i, target in enumerate(range(1, 121))},
        index=data_with_features.index[-len(X_new_sequences):]
    )

    return predictions

def calculate_leverage(target: int) -> float:
    return max(15, min(100, 15 + (100 - 15) * (120 - target) / 119))


def calculate_risk_reward(prediction: float, threshold: float = 0.4) -> float:
    return abs(prediction - threshold) / threshold

def is_emergency_condition_rr(risk_reward: float, threshold: float = 10) -> bool:
    return risk_reward > threshold

def add_technical_indicators(data: pd.DataFrame) -> pd.DataFrame:
    data['MA200'] = talib.SMA(data['Close'], timeperiod=MOVING_AVERAGE_PERIOD)
    data['RSI'] = talib.RSI(data['Close'], timeperiod=RSI_PERIOD)
    macd, signal, _ = talib.MACD(data['Close'], fastperiod=MACD_FAST, slowperiod=MACD_SLOW, signalperiod=MACD_SIGNAL)
    data['MACD'] = macd
    data['MACD_Signal'] = signal
    return data

def determine_market_trend(data: pd.DataFrame) -> str:
    current_price = data['Close'].iloc[-1]
    ma200 = data['MA200'].iloc[-1]
    if current_price > ma200:
        return "bullish"
    elif current_price < ma200:
        return "bearish"
    else:
        return "neutral"

def is_overbought_oversold(data: pd.DataFrame) -> str:
    rsi = data['RSI'].iloc[-1]
    if rsi > RSI_OVERBOUGHT:
        return "overbought"
    elif rsi < RSI_OVERSOLD:
        return "oversold"
    else:
        return "neutral"

def calculate_position_size(account_balance: float, entry_price: float, stop_loss: float) -> float:
    risk_amount = account_balance * RISK_PER_TRADE
    position_size = risk_amount / abs(entry_price - stop_loss)
    return position_size

def trading_strategy(data: pd.DataFrame, predictions: pd.DataFrame, account_balance: float) -> None:
    global position, trades
    current_price = data['Close'].iloc[-1]
    market_trend = determine_market_trend(data)
    overbought_oversold = is_overbought_oversold(data)
    summary = []

    num_positive_predictions = (predictions > 0.4).sum().sum()
    num_negative_predictions = (predictions < -0.4).sum().sum()
    total_predictions = predictions.shape[1]

    for i in range(1, 121):
        prediction = predictions[f'T_{i}'].iloc[-1]
        leverage = calculate_leverage(i)
        risk_reward = calculate_risk_reward(prediction)

        summary.append(f"T_{i}: {prediction:.4f}, Leverage: {leverage}, R/R: {risk_reward:.4f}")

        if position is None:
            if prediction > 0.4 and num_positive_predictions / total_predictions >= 0.9 and market_trend == "bullish" and overbought_oversold != "overbought":
                stop_loss = current_price * 0.99  # 1% stop loss
                position_size = calculate_position_size(account_balance, current_price, stop_loss)
                position = {
                    'type': 'buy',
                    'amount': position_size,
                    'entry_price': current_price,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'stop_loss': stop_loss
                }
                trades.append({
                    'action': 'buy',
                    'price': current_price,
                    'amount': position_size,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'time': data['timestamp'].iloc[-1]
                })
                summary.append(f"Buying at {current_price} with leverage {leverage}, R/R {risk_reward}, and position size {position_size} based on T_{i} prediction of {prediction}")
                break
            elif prediction < -0.4 and num_negative_predictions / total_predictions >= 0.9 and market_trend == "bearish" and overbought_oversold != "oversold":
                stop_loss = current_price * 1.01  # 1% stop loss
                position_size = calculate_position_size(account_balance, current_price, stop_loss)
                position = {
                    'type': 'sell',
                    'amount': position_size,
                    'entry_price': current_price,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'stop_loss': stop_loss
                }
                trades.append({
                    'action': 'sell',
                    'price': current_price,
                    'amount': position_size,
                    'leverage': leverage,
                    'risk_reward': risk_reward,
                    'time': data['timestamp'].iloc[-1]
                })
                summary.append(f"Selling at {current_price} with leverage {leverage}, R/R {risk_reward}, and position size {position_size} based on T_{i} prediction of {prediction}")
                break
        else:
            if position['type'] == 'buy':
                if current_price <= position['stop_loss'] or prediction < -0.4 or is_emergency_condition_rr(risk_reward):
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
                if current_price >= position['stop_loss'] or prediction > 0.4 or is_emergency_condition_rr(risk_reward):
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

    logging.info("\n".join(summary))

def fetch_ohlcv_data(exchange: ccxt.Exchange, symbol: str, timeframe: str, since: int) -> List:
    ohlcv = []
    while since < exchange.milliseconds():
        data = exchange.fetch_ohlcv(symbol, timeframe, since=since)
        if not data:
            break
        ohlcv.extend(data)
        since = data[-1][0] + 1
    return ohlcv

def main():
    exchange = ccxt.bingx()
    account_balance = 10000  # Initial account balance, you should update this with actual balance

    while True:
        try:
            now = datetime.utcnow()
            seven_days_ago = now - timedelta(days=7)
            since = exchange.parse8601(seven_days_ago.isoformat())

            ohlcv = fetch_ohlcv_data(exchange, SYMBOL, TIMEFRAME, since)

            data = pd.DataFrame(ohlcv, columns=['timestamp', 'Open', 'High', 'Low', 'Close', 'Volume'])
            data['timestamp'] = pd.to_datetime(data['timestamp'], unit='ms')

            data = add_technical_indicators(data)

            predictions = predict_new_data(model, scaler_X, scaler_y, data, look_back=LOOK_BACK)

            trading_strategy(data, predictions, account_balance)

            logging.info(f"Datetime in last row: {data['timestamp'].iloc[-1]}")
            logging.info(f"Current position: {position}")
            logging.info(f"Trades: {trades}")
            logging.info(f"Market Trend: {determine_market_trend(data)}")
            logging.info(f"Overbought/Oversold: {is_overbought_oversold(data)}")

        except Exception as e:
            logging.error(f"An error occurred: {e}")

        time.sleep(25)

if __name__ == "__main__":
    main()
