import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, LSTM, Dense, Dropout, Bidirectional
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import logging
from typing import List, Tuple

logging.basicConfig(level=logging.INFO)

def setup_gpu():
    gpus = tf.config.experimental.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
            logging.info("GPUs are configured for memory growth.")
        except RuntimeError as e:
            logging.error(f"Error configuring GPU: {e}")
    else:
        logging.warning("No GPU available, using CPU instead.")

def calculate_technical_indicators(data: pd.DataFrame, periods: List[int]) -> pd.DataFrame:
    for N in periods:
        data[f'hl_{N}'] = ((data['High'].rolling(window=N).max() - data['Low'].rolling(window=N).min()) / data['Low'].rolling(window=N).min()) * 100
        data[f'p_{N}'] = ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100
        data = calculate_fft(data, N)
    return data

def calculate_fft(data: pd.DataFrame, N: int) -> pd.DataFrame:
    close_fft = np.fft.fft(np.asarray(data['Close'].tolist()))
    fft_df = pd.DataFrame({'fft': close_fft})
    fft_df['fft_real'] = fft_df['fft'].apply(lambda x: np.real(x))
    fft_df['fft_imag'] = fft_df['fft'].apply(lambda x: np.imag(x))
    fft_df = fft_df[['fft_real', 'fft_imag']]
    fft_df.columns = [f'fft_{N}_real', f'fft_{N}_imag']
    return pd.concat([data.reset_index(drop=True), fft_df], axis=1)

def calculate_targets(data: pd.DataFrame, target_periods: List[int]) -> pd.DataFrame:
    targets = pd.DataFrame(index=data.index)
    for period in target_periods:
        targets[f'T_{period}'] = data['Close'].pct_change().shift(-period).rolling(window=period).sum() * 100
    return targets

def create_model(input_shape: Tuple[int, int], output_shape: int) -> Model:
    input_layer = Input(shape=input_shape)
    x = Bidirectional(LSTM(512, return_sequences=True))(input_layer)
    x = Dropout(0.3)(x)
    x = Bidirectional(LSTM(256))(x)
    x = Dropout(0.3)(x)
    output_layer = Dense(output_shape, activation='linear')(x)
    model = Model(inputs=input_layer, outputs=output_layer)
    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001), loss='mse')
    return model

def prepare_sequences(X: np.ndarray, y: np.ndarray, look_back: int) -> Tuple[np.ndarray, np.ndarray]:
    X_sequences = np.array([X[i:i + look_back] for i in range(len(X) - look_back + 1)])
    y_sequences = y[look_back - 1:]
    return X_sequences, y_sequences

def train_and_evaluate(X: np.ndarray, y: np.ndarray, look_back: int, target_periods: List[int]) -> Model:
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = create_model((look_back, X.shape[2]), y.shape[1])
    
    callbacks = [
        EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True),
        ModelCheckpoint('best_model.h5', save_best_only=True),
        ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=10, min_lr=0.0001)
    ]

    with tf.device('/GPU:0'):
        history = model.fit(
            X_train, y_train, 
            validation_data=(X_test, y_test), 
            epochs=500, 
            batch_size=256,
            callbacks=callbacks
        )

    y_pred = model.predict(X_test)
    evaluate_model(y_test, y_pred, target_periods)
    
    model.save('BILSTM_model.h5')
    logging.info("Model saved as 'BILSTM_model.h5'")
    return model

def evaluate_model(y_true: np.ndarray, y_pred: np.ndarray, target_periods: List[int]):
    mae = mean_absolute_error(y_true, y_pred)
    mse = mean_squared_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred, multioutput='raw_values')

    logging.info(f"Final evaluation results - MAE: {mae}, MSE: {mse}")
    for i, period in enumerate(target_periods):
        logging.info(f"R2 score for T_{period}: {r2[i]}")

def main(data_path: str):
    setup_gpu()
    data = pd.read_csv(data_path)
    data.dropna(inplace=True)

    periods = [1, 2, 3, 5, 10, 20, 30, 60, 90, 120, 180, 360, 720]
    target_periods = list(range(1, 91))

    data = calculate_technical_indicators(data, periods)
    targets = calculate_targets(data, target_periods)

    data = pd.concat([data, targets], axis=1).dropna()

    numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
    X = data[numeric_cols].drop([f'T_{p}' for p in target_periods], axis=1).values
    y = data[[f'T_{p}' for p in target_periods]].values

    scaler_X = StandardScaler()
    scaler_y = StandardScaler()
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y)

    look_back = 90
    X_sequences, y_sequences = prepare_sequences(X_scaled, y_scaled, look_back)

    model = train_and_evaluate(X_sequences, y_sequences, look_back, target_periods)
    
    joblib.dump(scaler_X, 'scaler_X.pkl')
    joblib.dump(scaler_y, 'scaler_y.pkl')
    logging.info("Scalers saved")

if __name__ == "__main__":
    main(r'D:\project\crypto my self\Data_Set\BTCUSDT_ohlc_data_1min.csv')
