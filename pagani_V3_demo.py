import pandas as pd
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Input, Bidirectional, LSTM, Dropout, Flatten, Dense
from tensorflow.keras.callbacks import EarlyStopping
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
from scipy.spatial.distance import pdist
from scipy import stats

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

def calculate_t_pct(data, N):
    return data['Close'].pct_change().shift(-N).rolling(window=N).sum() * 100

def hadamard_transform(prices, period):
    """Apply Hadamard transform to closing prices over a single period."""
    def hadamard_matrix(n):
        """Generate an n x n Hadamard matrix."""
        if n == 1:
            return np.array([[1]])
        else:
            H = hadamard_matrix(n // 2)
            return np.block([[H, H], [H, -H]]) / np.sqrt(2)
    
    if len(prices) >= period:
        if (period & (period - 1)) == 0:  # Check if period is a power of 2
            subset = prices[-period:]
            H = hadamard_matrix(len(subset))
            transformed = np.dot(H, subset)
            return transformed
        else:
            return np.zeros(period)  # Return zeros if period is not a power of 2
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

# توابع جدید
def calculate_hl_N(data, N):
    high = data['High'].rolling(window=N).max()
    low = data['Low'].rolling(window=N).min()
    return ((high - low) / low) * 100

def calculate_p_N(data, N):
    return ((data['Close'] - data['Close'].shift(N)) / data['Close'].shift(N)) * 100

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
    print("Loading data...")
    data = pd.read_csv(data_path)
    data.dropna(inplace=True)

    # Define periods for quantum features
    quantum_periods = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]
    # Define periods for other features
    periods = [2, 4, 8, 16, 32, 64, 128, 256, 512, 1024]

    print("Calculating quantum features...")
    # Calculate quantum features for each period and add as separate columns
    for period in quantum_periods:
        print(f"Calculating Quantum Feature for period: {period}")
        if (period & (period - 1)) == 0:  # Check if period is a power of 2
            data[f'Quantum_Feature_{period}'] = data['Close'].rolling(window=period).apply(
                lambda x: hadamard_transform(x, period)[-1] if len(x) == period else np.nan
            ).fillna(0)
        else:
            data[f'Quantum_Feature_{period}'] = np.zeros(len(data))

    print("Calculating additional features...")
    # Calculate additional features
    for period in periods:
        print(f"Calculating Brownian Motion for period: {period}")
        data[f'Brownian_Motion_{period}'] = calculate_brownian_motion(data, period)
        print(f"Calculating Entropy for period: {period}")
        data[f'Entropy_{period}'] = calculate_entropy(data, period)
        print(f"Calculating Fractal Dimension for period: {period}")
        data[f'Fractal_Dimension_{period}'] = calculate_fractal_dimension(data, period)
        print(f"Calculating HL_N for period: {period}")
        data[f'HL_N_{period}'] = calculate_hl_N(data, period)
        print(f"Calculating P_N for period: {period}")
        data[f'P_N_{period}'] = calculate_p_N(data, period)

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
    print("Scaling data...")
    X_scaled = scaler_X.fit_transform(X)
    y_scaled = scaler_y.fit_transform(y)

    # Ensure consistent length by truncating y
    max_lookback = 90
    X_scaled = X_scaled[max_lookback - 1:]
    y_scaled = y_scaled[max_lookback - 1:]

    print("Creating sequences...")
    X_sequences = np.array([X_scaled[i:i + 90] for i in range(len(X_scaled) - 89)])
    y_sequences = y_scaled[89:]

    print("Training and evaluating model...")
    model = train_and_evaluate(X_sequences, y_sequences, look_back=90, target_periods=target_periods)
    joblib.dump(scaler_X, 'scaler_X.pkl')
    joblib.dump(scaler_y, 'scaler_y.pkl')
    print("Scalers saved")

def train_and_evaluate(X, y, look_back, target_periods):
    print("Splitting data...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.01, random_state=42)
    print("Creating model...")
    model = create_model((look_back, X.shape[2]), y.shape[1])
    early_stopping = EarlyStopping(monitor='val_loss', patience=20, restore_best_weights=True)

    print("Starting model training...")
    with tf.device('/GPU:0'):
        model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=450, batch_size=64,
                  callbacks=[early_stopping])

    print("Predicting...")
    y_pred = model.predict(X_test)
    mae = mean_absolute_error(y_test, y_pred)
    mse = mean_squared_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred, multioutput='raw_values')

    print(f"Final evaluation results - MAE: {mae}, MSE: {mse}")
    for i, period in enumerate(target_periods):
        print(f"R2 score for T_{period}: {r2[i]}")

    print("Saving model...")
    model.save('BILSTM_model.h5')
    print("Model saved as 'bilstm_model.h5'")

    return model

if __name__ == "__main__":
    main(r'BTCUSDT_ohlc_data_1min.csv')
