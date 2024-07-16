import pandas as pd
import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Bidirectional, Flatten, Attention
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from scipy.stats import skew, kurtosis

# Enable GPU growth to prevent TensorFlow from consuming all GPU memory
physical_devices = tf.config.list_physical_devices('GPU')
if physical_devices:
    try:
        for device in physical_devices:
            tf.config.experimental.set_memory_growth(device, True)
        print(f"{len(physical_devices)} GPU(s) available and memory growth set.")
    except RuntimeError as e:
        print(f"Error setting GPU memory growth: {e}")
else:
    print("No GPU available. Using CPU.")

os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'


def calculate_hl_N(data, N):
    high = data['High'].rolling(window=N).max()
    low = data['Low'].rolling(window=N).min()
    return ((high - low) / low) * 100


def calculate_p_N(data, N):
    return ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100


def calculate_t_pct(data, N):
    return data['Close'].pct_change().shift(-N).rolling(window=N).sum() * 100


def calculate_ema(data, N):
    return data['Close'].ewm(span=N, adjust=False).mean()


def calculate_fibonacci_retracement(data, window):
    high = data['High'].rolling(window=window).max()
    low = data['Low'].rolling(window=window).min()
    diff = high - low
    levels = {
        f'fib_0.236_{window}': high - 0.236 * diff,
        f'fib_0.382_{window}': high - 0.382 * diff,
        f'fib_0.618_{window}': high - 0.618 * diff,
    }
    return levels


def calculate_swing_high_low(data, window):
    swing_high = data['High'][
        data['High'].rolling(window=window, center=True).apply(lambda x: x.argmax()) == window // 2]
    swing_low = data['Low'][data['Low'].rolling(window=window, center=True).apply(lambda x: x.argmin()) == window // 2]
    swing_high = swing_high.reindex(data.index).fillna(method='bfill').fillna(method='ffill')
    swing_low = swing_low.reindex(data.index).fillna(method='bfill').fillna(method='ffill')
    return swing_high, swing_low


def calculate_custom_moving_average(data, window):
    custom_ma = data['Close'].rolling(window=window).apply(lambda x: np.mean(np.diff(x)))
    return custom_ma


def calculate_roc(data, window):
    roc = data['Close'].diff(window) / data['Close'].shift(window)
    return roc


def add_custom_features(data):
    custom_features = {}
    # Add Fibonacci retracement levels
    fib_levels = calculate_fibonacci_retracement(data, 20)
    custom_features.update(fib_levels)

    # Add swing high/low
    swing_high, swing_low = calculate_swing_high_low(data, 10)
    custom_features['swing_high_10'] = swing_high
    custom_features['swing_low_10'] = swing_low

    # Add custom moving average
    custom_features['custom_ma_10'] = calculate_custom_moving_average(data, 10)

    # Add rate of change
    custom_features['roc_10'] = calculate_roc(data, 10)

    return custom_features


def add_pump_and_dump_features(data, N):
    features = {
        'volume_spike': (data['Volume'] / data['Volume'].rolling(window=N).mean()).fillna(0),
        'price_spike': (data['Close'].pct_change().abs() / data['Close'].pct_change().abs().rolling(
            window=N).mean()).fillna(0)
    }
    return features


def add_static_features(data):
    mean_close = data['Close'].mean()
    std_close = data['Close'].std()
    skew_close = skew(data['Close'])
    kurtosis_close = kurtosis(data['Close'])
    initial_open = data['Open'].iloc[0]
    initial_high = data['High'].iloc[0]
    initial_low = data['Low'].iloc[0]
    initial_close = data['Close'].iloc[0]

    mean_volume = data['Volume'].mean()
    std_volume = data['Volume'].std()

    static_features = {
        'static_features_1': mean_close + std_close + skew_close + kurtosis_close + initial_open + initial_high + initial_low + initial_close,
        'static_features_2': mean_volume + std_volume
    }
    return static_features


def build_model(input_shape, output_shape, lstm_units=100, dropout_rate=0.3, learning_rate=0.0005):
    input_layer = Input(shape=input_shape)
    x = Bidirectional(LSTM(lstm_units, return_sequences=True))(input_layer)

    attention = Attention()([x, x])  # Only one output from Attention

    x = Dropout(dropout_rate)(attention)
    x = Flatten()(x)
    x = Dense(100, activation='relu')(x)
    x = Dropout(dropout_rate)(x)
    output_layer = Dense(output_shape, activation='linear')(x)

    model = Model(inputs=input_layer, outputs=output_layer)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate), loss='mse')
    return model


def main(data_path):
    data = pd.read_csv(data_path, parse_dates=['timestamp'], index_col='timestamp')
    data.dropna(inplace=True)

    # Calculate indicators
    periods = [1, 2, 3, 5, 10, 20, 30, 40, 60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900,
               960, 1020, 1080, 1140, 1200, 1260, 1320, 1380, 1440]
    new_features = {}
    for N in periods:
        new_features[f'ema_{N}'] = calculate_ema(data, N)
        new_features[f'hl_{N}'] = calculate_hl_N(data, N)
        new_features[f'p_{N}'] = calculate_p_N(data, N)

    new_features.update(add_pump_and_dump_features(data, 10))
    new_features.update(add_static_features(data))
    new_features.update(add_custom_features(data))

    # Add all new features to the dataframe at once
    data = pd.concat([data, pd.DataFrame(new_features, index=data.index)], axis=1)

    # Prepare targets
    target_periods = list(range(1, 181))
    targets = pd.DataFrame(index=data.index)
    target_data = {f'T_{period}': calculate_t_pct(data, period) for period in target_periods}
    targets = pd.concat([targets, pd.DataFrame(target_data)], axis=1)

    data = pd.concat([data, targets], axis=1).dropna()

    # Ensure only numeric data is considered
    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    X = data[numeric_cols].drop([f'T_{p}' for p in target_periods], axis=1).values
    y = data[[f'T_{p}' for p in target_periods]].values

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y)

    # Ensure consistent length by truncating y
    max_lookback = 180  # Update lookback period to 180
    X_scaled = X_scaled[max_lookback - 1:]
    y_scaled = y_scaled[max_lookback - 1:]

    X_sequences = np.array([X_scaled[i:i + 180] for i in range(len(X_scaled) - 179)])
    y_sequences = y_scaled[179:]

    # Build and train the model
    model = build_model(input_shape=(180, X_sequences.shape[2]), output_shape=y_sequences.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, restore_best_weights=True)
    
    history = model.fit(
        X_sequences, y_sequences,
        validation_split=0.2,
        epochs=50,
        batch_size=128,
        callbacks=[early_stopping],
        verbose=1
    )

    # Save the model and scalers
    joblib.dump(scaler_X, 'scaler_X.pkl')
    joblib.dump(scaler_y, 'scaler_y.pkl')
    model.save('best_bilstm_model.h5')
    print("Best model saved as 'best_bilstm_model.h5'")


if __name__ == "__main__":
    main(r'BTCUSDT_ohlc_data_1min.csv')
