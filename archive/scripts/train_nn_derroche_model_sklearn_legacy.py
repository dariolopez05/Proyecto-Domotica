#!/usr/bin/env python3
"""
Entrena una red neuronal (MLP) para clasificacion binaria de derroche en la siguiente hora.
Dataset de entrada: data/gold/dataset_final_ia.csv
"""

from __future__ import annotations

from pathlib import Path
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

DATA_FILE = BASE_DIR / "data" / "silver" / "master_dataset.csv"
MODEL_FILE = BASE_DIR / "models" / "nn_derroche_model.joblib"
METRICS_FILE = BASE_DIR / "reports" / "nn_derroche_metrics.txt"
PRED_FILE = BASE_DIR / "data" / "gold" / "nn_derroche_predictions.csv"


def main() -> None:
    if not DATA_FILE.exists():
        raise FileNotFoundError(f"No existe {DATA_FILE}")

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PRED_FILE.parent.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_FILE)
    feature_cols = [
        "hora_sin",
        "hora_cos",
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
    y = (
        df[target_col]
        .map({True: 1, False: 0, "True": 1, "False": 0, "1": 1, "0": 0})
        .fillna(0)
        .astype(int)
    )

    for col in feature_cols:
        X[col] = pd.to_numeric(X[col], errors="coerce")

    # Holdout temporal 80/20 (sin barajar).
    split_idx = int(len(df) * 0.8)
    if split_idx < 100:
        raise RuntimeError("Muy pocos datos para entrenamiento/evaluacion de NN.")
    X_train = X.iloc[:split_idx]
    y_train = y.iloc[:split_idx]
    X_test = X.iloc[split_idx:]
    y_test = y.iloc[split_idx:]

    pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            # Sin leakage: scaler ajustado solo con train al hacer pipeline.fit(X_train, y_train)
            ("scaler", StandardScaler()),
            (
                "model",
                MLPClassifier(
                    # Alineado con la arquitectura del notebook (Dense 64 relu + Dense 32 relu),
                    # adaptada a un problema binario.
                    hidden_layer_sizes=(64, 32),
                    activation="relu",
                    solver="adam",
                    alpha=1e-4,
                    learning_rate_init=1e-3,
                    max_iter=600,
                    random_state=42,
                ),
            ),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]

    acc = float(accuracy_score(y_test, y_pred))
    f1 = float(f1_score(y_test, y_pred, zero_division=0))
    roc = float(roc_auc_score(y_test, y_proba)) if y_test.nunique() > 1 else float("nan")
    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(y_test, y_pred, digits=4, zero_division=0)

    payload = {
        "pipeline": pipeline,
        "features": feature_cols,
        "target": target_col,
    }
    joblib.dump(payload, MODEL_FILE)

    pred_df = df.iloc[split_idx:].copy()
    pred_df["pred_derroche_next_hour"] = y_pred
    pred_df["pred_derroche_next_hour_proba"] = y_proba
    pred_df.to_csv(PRED_FILE, index=False)

    metrics = "\n".join(
        [
            "RED NEURONAL (MLP) - DERROCHE SIGUIENTE HORA",
            f"Filas train: {len(X_train)}",
            f"Filas test: {len(X_test)}",
            f"Features: {', '.join(feature_cols)}",
            "",
            f"Accuracy: {acc:.4f}",
            f"F1-score: {f1:.4f}",
            f"ROC-AUC: {roc:.4f}",
            "",
            "Matriz de confusion [ [TN, FP], [FN, TP] ]:",
            str(cm.tolist()),
            "",
            "Classification report:",
            report,
            "",
            f"Modelo guardado: {MODEL_FILE}",
            f"Predicciones test: {PRED_FILE}",
        ]
    )
    METRICS_FILE.write_text(metrics, encoding="utf-8")
    print(f"OK NN derroche. Accuracy={acc:.4f} F1={f1:.4f} ROC-AUC={roc:.4f}")


if __name__ == "__main__":
    main()
