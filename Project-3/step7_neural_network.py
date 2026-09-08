import joblib
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, callbacks
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.utils.class_weight import compute_class_weight

X_train, X_test, y_train, y_test = joblib.load('outputs/train_test_split_dl.pkl')

X_train = X_train.astype('float32').values
X_test = X_test.astype('float32').values
y_train = y_train.values
y_test = y_test.values

model = keras.Sequential([
    layers.Dense(128, activation='relu', input_shape=(X_train.shape[1],)),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(64, activation='relu'),
    layers.BatchNormalization(),
    layers.Dropout(0.3),
    layers.Dense(32, activation='relu'),
    layers.Dropout(0.2),
    layers.Dense(1, activation='sigmoid'),
])
model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.001),
    loss='binary_crossentropy',
    metrics=['accuracy', keras.metrics.AUC(name='auc')]
)
model.summary()

early_stop = callbacks.EarlyStopping(monitor='val_auc', patience=10, restore_best_weights=True, mode='max')
reduce_lr = callbacks.ReduceLROnPlateau(monitor='val_loss', factor=0.5, patience=5)

class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = dict(enumerate(class_weights))
print('Class weights:', class_weight_dict)

history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=256,
    class_weight=class_weight_dict,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)


y_prob_nn = model.predict(X_test).flatten()
y_pred_nn = (y_prob_nn >= 0.5).astype(int)

print(f'Accuracy: {accuracy_score(y_test, y_pred_nn):.4f}')
print(f'AUC-ROC: {roc_auc_score(y_test, y_prob_nn):.4f}')
print(classification_report(y_test, y_pred_nn, target_names=['Ineffective', 'Effective']))


model.save('outputs/neural_network_model.keras')
np.save('outputs/nn_y_prob.npy', y_prob_nn)
np.save('outputs/nn_y_test.npy', y_test)
print('Saved model and predictions')
