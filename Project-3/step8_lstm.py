import joblib
import numpy as np
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split_dl.pkl')

X_train = X_train.astype('float32').values
X_test = X_test.astype('float32').values
y_train = y_train.values
y_test = y_test.values

n_timesteps, n_features = 6, 29
assert n_timesteps * n_features == X_train.shape[1], "column count changed — recheck the factor pair"

X_train_seq = X_train.reshape(-1, n_timesteps, n_features)
X_test_seq = X_test.reshape(-1, n_timesteps, n_features)
print('Reshaped:', X_train_seq.shape, X_test_seq.shape)


lstm_model = keras.Sequential([
    layers.LSTM(64, return_sequences=True, input_shape=(n_timesteps, n_features)),
    layers.Dropout(0.3),
    layers.LSTM(32, return_sequences=False),
    layers.Dropout(0.3),
    layers.Dense(16, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid'),
])
lstm_model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)
lstm_model.summary()


early_stop = callbacks.EarlyStopping(monitor='val_auc', patience=10, restore_best_weights=True, mode='max')
reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)

class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(enumerate(class_weights))


history = lstm_model.fit(
    X_train_seq, y_train,
    validation_split=0.2,
    epochs=50,
    batch_size=256,
    class_weight=class_weight_dict,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)


y_prob_lstm = lstm_model.predict(X_test_seq).flatten()
y_pred_lstm = (y_prob_lstm >= 0.5).astype(int)

print(f'Accuracy: {accuracy_score(y_test, y_pred_lstm):.4f}')
print(f'AUC-ROC: {roc_auc_score(y_test, y_prob_lstm):.4f}')
print(classification_report(y_test, y_pred_lstm, target_names=['Ineffective', 'Effective']))

lstm_model.save('outputs/lstm_model.keras')
np.save('outputs/lstm_y_prob.npy', y_prob_lstm)
print('Saved LSTM model and predictions')