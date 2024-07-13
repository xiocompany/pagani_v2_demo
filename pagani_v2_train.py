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
    main(r'D:\project\crypto my self\Data_Set\BTCUSDT_ohlc_data_1min.csv')
