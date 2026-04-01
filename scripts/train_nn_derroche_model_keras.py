#!/usr/bin/env python3
"""
Entrena una red neuronal con TensorFlow/Keras para clasificacion binaria de
derroche en la siguiente hora.

Entrada:  data/gold/dataset_final_ia.csv (capa Gold)
Salida:
  - models/nn_derroche_model_keras.keras
  - models/nn_derroche_preprocess_keras.joblib (imputer+scaler+features)
  - reports/nn_derroche_metrics_keras.txt
  - data/gold/nn_derroche_predictions_keras.csv
"""

from __future__ import annotations

from pathlib import Path
import os
import random
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.config import DATASET_FINAL_IA_CSV, NN_DERROCHE_PREDICTIONS_KERAS_CSV

DATA_FILE = DATASET_FINAL_IA_CSV
MODEL_FILE = BASE_DIR / "models" / "nn_derroche_model_keras.keras"
PREPROCESS_FILE = BASE_DIR / "models" / "nn_derroche_preprocess_keras.joblib"
METRICS_FILE = BASE_DIR / "reports" / "nn_derroche_metrics_keras.txt"
BACKTEST_FILE = BASE_DIR / "reports" / "nn_derroche_backtest_keras.txt"
PRED_FILE = NN_DERROCHE_PREDICTIONS_KERAS_CSV


def set_seeds(seed: int = 42) -> None:
    os.environ["PYTHONHASHSEED"] = str(seed)
    random.seed(seed)
    np.random.seed(seed)
    try:
        import tensorflow as tf  # noqa: WPS433

        tf.random.set_seed(seed)
    except Exception:
        # si TF no esta disponible, el script fallara mas abajo al importarlo
        pass


def main() -> None:
    set_seeds(42)

    if not DATA_FILE.exists():
        raise FileNotFoundError(f"No existe {DATA_FILE}")

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    BACKTEST_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRED_FILE.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_FILE)

    feature_cols = [
        "hora_sin",
        "hora_cos",
        "dia_semana_sin",
        "dia_semana_cos",
        "mes_sin",
        "mes_cos",
        "temp_aula",
        "temp_ext",
        "humedad_aula",
        "viento",
        "nubosidad",
        "sol_elevacion",
        "porcentaje_ventilacion_aula",
    ]
    target_col = "target_derroche_next_hour"

    missing = [c for c in feature_cols + [target_col] if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en dataset_final_ia.csv: {missing}")

    X = df[feature_cols].copy()
    for col in feature_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    y = (
        df[target_col]
        .map({True: 1, False: 0, "True": 1, "False": 0, "1": 1, "0": 0, 1: 1, 0: 0})
        .astype(int)
    )

    # Holdout temporal 80/20 (sin barajar)
    split_idx = int(len(df) * 0.8)
    if split_idx < 100:
        raise RuntimeError("Muy pocos datos para entrenamiento/evaluacion de NN.")

    X_train_raw = X.iloc[:split_idx].to_numpy(dtype=np.float32)
    y_train = y.iloc[:split_idx].to_numpy(dtype=np.int32)
    X_test_raw = X.iloc[split_idx:].to_numpy(dtype=np.float32)
    y_test = y.iloc[split_idx:].to_numpy(dtype=np.int32)

    import tensorflow as tf
    from tensorflow import keras

    def build_model(input_dim: int) -> keras.Model:
        m = keras.Sequential(
            [
                keras.layers.Input(shape=(input_dim,)),
                keras.layers.Dense(64, activation="relu"),
                keras.layers.Dense(32, activation="relu"),
                keras.layers.Dense(1, activation="sigmoid"),
            ]
        )
        m.compile(
            optimizer=keras.optimizers.Adam(learning_rate=1e-3),
            loss="binary_crossentropy",
            metrics=[
                keras.metrics.BinaryAccuracy(name="accuracy"),
                keras.metrics.AUC(name="auc"),
                keras.metrics.Precision(name="precision"),
                keras.metrics.Recall(name="recall"),
            ],
        )
        return m

    def pick_threshold_max_f1(y_true: np.ndarray, proba: np.ndarray) -> tuple[float, float]:
        thresholds = np.linspace(0.05, 0.95, 19, dtype=np.float32)
        best_thr = 0.5
        best = -1.0
        for thr in thresholds:
            pred = (proba >= float(thr)).astype(int)
            score = float(f1_score(y_true, pred, zero_division=0))
            if score > best:
                best = score
                best_thr = float(thr)
        return best_thr, best

    # Backtest temporal (walk-forward manual) sobre el 80% train.
    # Motivo: la clase positiva puede estar concentrada al final y TimeSeriesSplit puede
    # generar ventanas sin positivos. Aqui forzamos ventanas de validacion en el tramo final.
    fold_rows: list[str] = []
    fold_metrics: list[dict[str, float]] = []

    total_train = len(y_train)
    total_pos = int((y_train == 1).sum())
    total_neg = int((y_train == 0).sum())

    val_size = max(200, int(total_train * 0.12))
    start_min = int(total_train * 0.55)
    start_max = total_train - val_size
    candidate_starts = np.linspace(start_min, start_max, num=5, dtype=int)
    candidate_starts = sorted(set(int(s) for s in candidate_starts))

    for fold, val_start in enumerate(candidate_starts, start=1):
        val_end = min(total_train, val_start + val_size)
        tr_end = val_start

        y_tr_fold = y_train[:tr_end]
        y_va_fold = y_train[val_start:val_end]
        pos_tr = int((y_tr_fold == 1).sum())
        neg_tr = int((y_tr_fold == 0).sum())
        pos_val = int((y_va_fold == 1).sum())
        neg_val = int((y_va_fold == 0).sum())

        if pos_tr < 1 or pos_val < 1:
            fold_rows.append(
                f"Fold {fold}: skip (train pos={pos_tr} neg={neg_tr}; val pos={pos_val} neg={neg_val}) "
                f"train_n={len(y_tr_fold)} val_n={len(y_va_fold)}"
            )
            continue

        X_tr_raw = X_train_raw[:tr_end]
        X_va_raw = X_train_raw[val_start:val_end]

        imp_f = SimpleImputer(strategy="median")
        X_tr_imp = imp_f.fit_transform(X_tr_raw)
        X_va_imp = imp_f.transform(X_va_raw)

        sc_f = StandardScaler()
        X_tr_f = sc_f.fit_transform(X_tr_imp)
        X_va_f = sc_f.transform(X_va_imp)

        cw = {0: 1.0, 1: float(neg_tr / pos_tr)}

        m = build_model(input_dim=len(feature_cols))
        cb = [
            keras.callbacks.EarlyStopping(
                monitor="val_auc",
                mode="max",
                patience=5,
                restore_best_weights=True,
            )
        ]
        m.fit(
            X_tr_f,
            y_tr_fold,
            validation_data=(X_va_f, y_va_fold),
            epochs=40,
            batch_size=32,
            verbose=0,
            callbacks=cb,
            class_weight=cw,
            shuffle=True,
        )

        va_proba = m.predict(X_va_f, verbose=0).reshape(-1)
        thr, f1_val_pick = pick_threshold_max_f1(y_va_fold, va_proba)
        va_pred = (va_proba >= thr).astype(int)

        acc = float(accuracy_score(y_va_fold, va_pred))
        f1 = float(f1_score(y_va_fold, va_pred, zero_division=0))
        prec = float(precision_score(y_va_fold, va_pred, zero_division=0))
        rec = float(recall_score(y_va_fold, va_pred, zero_division=0))
        roc = float(roc_auc_score(y_va_fold, va_proba)) if len(np.unique(y_va_fold)) > 1 else float("nan")

        fold_metrics.append(
            {
                "acc": acc,
                "f1": f1,
                "precision": prec,
                "recall": rec,
                "roc_auc": roc,
                "thr": float(thr),
                "f1_val_pick": float(f1_val_pick),
            }
        )
        fold_rows.append(
            f"Fold {fold}: train_n={len(y_tr_fold)} val_n={len(y_va_fold)} "
            f"pos_val={pos_val} thr={thr:.2f} acc={acc:.4f} f1={f1:.4f} "
            f"prec={prec:.4f} rec={rec:.4f} roc_auc={roc:.4f}"
        )

    if fold_metrics:
        mean = {k: float(np.nanmean([m[k] for m in fold_metrics])) for k in fold_metrics[0].keys()}
        std = {k: float(np.nanstd([m[k] for m in fold_metrics])) for k in fold_metrics[0].keys()}
        backtest = "\n".join(
            [
                "BACKTEST TEMPORAL (walk-forward manual) - Keras derroche",
                f"Dataset (train 80%): {total_train} filas, pos={total_pos} neg={total_neg}",
                f"Val window size: {val_size} (aprox {val_size/total_train:.1%} del train)",
                "",
                *fold_rows,
                "",
                "Media (folds): "
                + " ".join([f"{k}={mean[k]:.4f}" for k in ["acc", "f1", "precision", "recall", "roc_auc", "thr"]]),
                "Std (folds):  "
                + " ".join([f"{k}={std[k]:.4f}" for k in ["acc", "f1", "precision", "recall", "roc_auc", "thr"]]),
            ]
        )
    else:
        backtest = "\n".join(
            [
                "BACKTEST TEMPORAL (walk-forward manual) - Keras derroche",
                f"Dataset (train 80%): {total_train} filas, pos={total_pos} neg={total_neg}",
                "",
                "Sin folds validos (val sin positivos en las ventanas candidatas).",
                "Sugerencia: ampliar ventana de validacion o revisar distribucion temporal del target.",
            ]
        )
    BACKTEST_FILE.write_text(backtest, encoding="utf-8")

    # Preprocesado sin leakage: fit SOLO en train
    imputer = SimpleImputer(strategy="median")
    X_train_imp = imputer.fit_transform(X_train_raw)
    X_test_imp = imputer.transform(X_test_raw)

    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train_imp)
    X_test = scaler.transform(X_test_imp)

    # Split de validacion temporal (dentro de train), sin barajar.
    # Buscamos un corte "cerca del final" que deje positivos y negativos en train y val.
    target_val_size = max(1, int(len(X_train) * 0.2))
    min_pos = 5
    min_neg = 5
    best_val_start: int | None = None
    best_gap = 10**9

    # probamos cortes en una banda amplia del final (manteniendo val al final)
    min_train_size = 200
    start_min = max(min_train_size, int(len(X_train) * 0.5))
    start_max = min(len(X_train) - 1, int(len(X_train) * 0.95))
    for val_start in range(start_max, start_min - 1, -1):
        y_tr_try = y_train[:val_start]
        y_val_try = y_train[val_start:]
        pos_tr = int((y_tr_try == 1).sum())
        neg_tr = int((y_tr_try == 0).sum())
        pos_val = int((y_val_try == 1).sum())
        neg_val = int((y_val_try == 0).sum())
        if pos_tr < min_pos or neg_tr < min_neg or pos_val < min_pos or neg_val < min_neg:
            continue
        gap = abs((len(X_train) - val_start) - target_val_size)
        if gap < best_gap:
            best_gap = gap
            best_val_start = val_start
            if gap == 0:
                break

    if best_val_start is None:
        raise RuntimeError(
            "No se pudo crear un split temporal train/val con suficientes positivos/negativos. "
            "Revisa distribucion temporal de la clase derroche."
        )

    X_tr, X_val = X_train[:best_val_start], X_train[best_val_start:]
    y_tr, y_val = y_train[:best_val_start], y_train[best_val_start:]

    model = build_model(input_dim=len(feature_cols))

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_auc",
            mode="max",
            patience=10,
            restore_best_weights=True,
        ),
    ]

    # Manejo de desbalanceo: pondera la clase positiva (derroche=1)
    pos = int((y_tr == 1).sum())
    neg = int((y_tr == 0).sum())
    if pos == 0:
        raise RuntimeError(
            "No hay ejemplos positivos (derroche=1) en el train interno tras ajustar validacion."
        )
    class_weight = {0: 1.0, 1: float(neg / pos)}

    model.fit(
        X_tr,
        y_tr,
        validation_data=(X_val, y_val),
        epochs=80,
        batch_size=32,
        verbose=1,
        callbacks=callbacks,
        class_weight=class_weight,
        shuffle=True,  # baraja SOLO el train interno (no baraja test ni val temporal)
    )

    # Evaluacion final en test
    val_proba = model.predict(X_val, verbose=0).reshape(-1)
    test_proba = model.predict(X_test, verbose=0).reshape(-1)

    best_thr, best_f1 = pick_threshold_max_f1(y_val, val_proba)

    y_proba = test_proba
    y_pred = (y_proba >= best_thr).astype(int)

    acc = float(accuracy_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    prec = float(precision_score(y_test, y_pred, zero_division=0))
    rec = float(recall_score(y_test, y_pred, zero_division=0))
    roc = float(roc_auc_score(y_test, y_proba)) if len(np.unique(y_test)) > 1 else float("nan")
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=4, zero_division=0)

    # Guardados
    model.save(MODEL_FILE)
    joblib.dump(
        {
            "imputer": imputer,
            "scaler": scaler,
            "features": feature_cols,
            "target": target_col,
            "threshold": best_thr,
        },
        PREPROCESS_FILE,
    )

    pred_df = df.iloc[split_idx:].copy()
    pred_df["pred_derroche_next_hour"] = y_pred
    pred_df["pred_derroche_next_hour_proba"] = y_proba
    pred_df.to_csv(PRED_FILE, index=False)

    metrics = "\n".join(
        [
            "RED NEURONAL (Keras) - DERROCHE SIGUIENTE HORA",
            f"Filas train: {len(X_train)} (train interno: {len(X_tr)} val: {len(X_val)})",
            f"Filas test: {len(X_test)}",
            f"Features: {', '.join(feature_cols)}",
            "",
            f"Umbral seleccionado (val): {best_thr:.2f} (mejor F1 val={best_f1:.4f})",
            "",
            f"Accuracy: {acc:.4f}",
            f"F1-score: {f1:.4f}",
            f"Precision: {prec:.4f}",
            f"Recall: {rec:.4f}",
            f"ROC-AUC: {roc:.4f}",
            "",
            "Matriz de confusion [ [TN, FP], [FN, TP] ]:",
            str(cm.tolist()),
            "",
            "Classification report:",
            report,
            "",
            f"Modelo guardado: {MODEL_FILE}",
            f"Prepro guardado: {PREPROCESS_FILE}",
            f"Predicciones test: {PRED_FILE}",
        ]
    )
    METRICS_FILE.write_text(metrics, encoding="utf-8")
    print(f"OK NN derroche (Keras). Accuracy={acc:.4f} F1={f1:.4f} ROC-AUC={roc:.4f}")


if __name__ == "__main__":
    main()

