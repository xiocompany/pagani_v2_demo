import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, GRU, Conv1D, MaxPooling1D, Flatten, Dense, Dropout, Bidirectional, LSTM
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from scipy.stats import skew, kurtosis


def setup_gpu():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            print("GPUs are configured for memory growth.")
        except RuntimeError as e:
            print(e)
    else:
        print("No GPU available, using CPU instead.")


def calculate_hl_N(data, N):
    high = data['High'].rolling(window=N).max()
    low = data['Low'].rolling(window=N).min()
    return ((high - low) / low) * 100


def calculate_p_N(data, N):
    return ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100


def calculate_t_pct(data, N):
    return data['Close'].pct_change().shift(-N).rolling(window=N).sum() * 100


def calculate_fft(data, N):
    close_fft = np.fft.fft(np.asarray(data['Close'].tolist()))
    fft_df = pd.DataFrame({'fft': close_fft})
    fft_df['fft_real'] = fft_df['fft'].apply(lambda x: np.real(x))
    fft_df['fft_imag'] = fft_df['fft'].apply(lambda x: np.imag(x))
    fft_df = fft_df[['fft_real', 'fft_imag']]
    fft_df.columns = [f'fft_{N}_real', f'fft_{N}_imag']
    data = pd.concat([data.reset_index(drop=True), fft_df], axis=1)
    return data


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


def create_model(input_shape, output_shape):
    input_layer = Input(shape=input_shape)
    x = Bidirectional(LSTM(509))(input_layer)
    x = Dropout(0.31111441165894993)(x)
    x = Flatten()(x)
    output_layer = Dense(output_shape, activation='linear')(x)
    model = Model(inputs=input_layer, outputs=output_layer)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0005363795781516295), loss='mse')
    return model


def main(data_path):
    setup_gpu()
    data = pd.read_csv(data_path)
    data.dropna(inplace=True)

    # Calculate indicators
    periods = [1, 2, 3, 5, 10, 20, 30, 40, 60, 90, 120, 180, 240, 300, 360, 420, 480, 540, 600, 660, 720, 780, 840, 900,
               960, 1020, 1080, 1140, 1200, 1260, 1320, 1380, 1440]
    for N in periods:
        data = calculate_fft(data, N)
        data[f'hl_{N}'] = calculate_hl_N(data, N)
        data[f'p_{N}'] = calculate_p_N(data, N)
        data[f'ema_{N}'] = calculate_ema(data, N)

    # Add custom features
    custom_features = add_custom_features(data)
    for feature_name, feature_values in custom_features.items():
        data[feature_name] = feature_values

    # Add pump and dump features
    pump_and_dump_features = add_pump_and_dump_features(data, 10)
    for feature_name, feature_values in pump_and_dump_features.items():
        data[feature_name] = feature_values

    # Add static features
    static_features = add_static_features(data)
    for feature_name, feature_value in static_features.items():
        data[feature_name] = feature_value

    # Prepare targets
    target_periods = list(range(1, 91))
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
    max_lookback = 90  # 60 for sequences and 720 for the maximum rolling window size
    X_scaled = X_scaled[max_lookback - 1:]
    y_scaled = y_scaled[max_lookback - 1:]

    X_sequences = np.array([X_scaled[i:i + 90] for i in range(len(X_scaled) - 89)])
    y_sequences = y_scaled[89:]

    model = train_and_evaluate(X_sequences, y_sequences, look_back=90, target_periods=target_periods)
    joblib.dump(scaler_X, 'scaler_X.pkl')
    joblib.dump(scaler_y, 'scaler_y.pkl')
    print("Scalers saved")


def train_and_evaluate(X, y, look_back, target_periods):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=42)
    model = create_model((look_back, X.shape[2]), y.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)

    with tf.device('/GPU:0'):
        model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=250, batch_size=256,
                  callbacks=[early_stopping])

    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred, multioutput='raw_values')

    print(f"Final evaluation results - MAE: {mae}, MSE: {mse}")
    for i, period in enumerate(target_periods):
        print(f"R2 score for T_{period}: {r2[i]}")

    model.save('BILSTM_model.h5')
    print("Model saved as 'bilstm_model.h5'")
    return model


if __name__ == "__main__":
    main(r'/content/BTCUSDT_ohlc_data_1min.csv')
