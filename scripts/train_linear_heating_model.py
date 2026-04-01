#!/usr/bin/env python3
"""
Entrena un modelo lineal para inferir temperatura de calefaccion y
anade la columna `temp_calefaccion_lineal` al gold principal.
"""

from __future__ import annotations

import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.config import BRONZE_HISTORY_CSV

MASTER_FILE = BASE_DIR / "data" / "gold" / "master_dataset.csv"
HISTORY_FILE = BRONZE_HISTORY_CSV
GOLD_ENRICHED_FILE = BASE_DIR / "data" / "gold" / "master_dataset.csv"
PREDICTIONS_FILE = BASE_DIR / "data" / "gold" / "heating_linear_predictions.csv"
MODEL_FILE = BASE_DIR / "models" / "heating_linear_model.joblib"
METRICS_FILE = BASE_DIR / "reports" / "heating_linear_model_metrics.txt"


def find_col(columns: list[str], includes: list[str]) -> str:
    lowered = {c.lower(): c for c in columns}
    for col_lower, original in lowered.items():
        if all(token in col_lower for token in includes):
            return original
    raise ValueError(f"No se encontro columna con tokens: {includes}")


def build_history_datetime(history: pd.DataFrame) -> pd.Series:
    date_col = find_col(history.columns.tolist(), ["date"])
    time_col = find_col(history.columns.tolist(), ["time"])
    return pd.to_datetime(
        history[date_col].astype(str) + " " + history[time_col].astype(str),
        format="%Y.%m.%d %H:%M",
        errors="coerce",
    )


def main() -> None:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"No existe {HISTORY_FILE}")
    if not GOLD_ENRICHED_FILE.exists():
        raise FileNotFoundError(f"No existe {GOLD_ENRICHED_FILE}")

    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)
    METRICS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)

    master = pd.read_csv(MASTER_FILE)
    gold = pd.read_csv(GOLD_ENRICHED_FILE)
    history = pd.read_csv(HISTORY_FILE)

    master["datetime"] = pd.to_datetime(master["datetime"], errors="coerce")
    gold["datetime"] = pd.to_datetime(gold["datetime"], errors="coerce")
    history["datetime"] = build_history_datetime(history)

    temp_col = find_col(history.columns.tolist(), ["temperature"])
    humidity_col = find_col(history.columns.tolist(), ["humidity"])
    history = history.rename(
        columns={
            temp_col: "temp_calefaccion_real",
            humidity_col: "humidity_history",
        }
    )
    history["temp_calefaccion_real"] = pd.to_numeric(history["temp_calefaccion_real"], errors="coerce")
    history["humidity_history"] = pd.to_numeric(history["humidity_history"], errors="coerce")

    master_features = [
        "datetime",
        "dia_semana",
        "mes",
        "hora",
        "temperatura_exterior",
        "humedad_exterior",
        "presion",
        "nubosidad",
        "viento",
        "direccion_viento",
        "azimuth_sol",
        "elevacion_sol",
        "temperatura_aula",
        "humedad_aula",
        "forecast",
    ]
    master_subset = master[[c for c in master_features if c in master.columns]].copy()
    df = history.merge(master_subset, on="datetime", how="left")
    df = df.dropna(subset=["datetime", "temp_calefaccion_real"]).sort_values("datetime")

    numeric_candidates = [
        "hora",
        "temperatura_exterior",
        "humedad_exterior",
        "presion",
        "nubosidad",
        "viento",
        "direccion_viento",
        "azimuth_sol",
        "elevacion_sol",
        "temperatura_aula",
        "humedad_aula",
        "humidity_history",
    ]
    for col in numeric_candidates:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    feature_cols = [
        "hora",
        "temperatura_exterior",
        "humedad_exterior",
        "presion",
        "nubosidad",
        "viento",
        "direccion_viento",
        "azimuth_sol",
        "elevacion_sol",
        "temperatura_aula",
        "humedad_aula",
        "humidity_history",
        "dia_semana",
        "mes",
        "forecast",
    ]
    feature_cols = [c for c in feature_cols if c in df.columns]
    if not feature_cols:
        raise RuntimeError("No hay features disponibles para entrenar el modelo lineal.")

    split_idx = int(len(df) * 0.8)
    if split_idx < 50:
        raise RuntimeError("Muy pocos datos para entrenar/evaluar el modelo lineal.")
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    X_train = train_df[feature_cols]
    y_train = train_df["temp_calefaccion_real"]
    X_test = test_df[feature_cols]
    y_test = test_df["temp_calefaccion_real"]

    numeric_features = X_train.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = [c for c in feature_cols if c not in numeric_features]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[("imputer", SimpleImputer(strategy="median"))]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ],
        remainder="drop",
    )

    # El modelo lineal es util aqui porque ofrece una relacion interpretable y estable
    # entre condiciones ambientales y temperatura inferida de calefaccion (tendencia base).
    model = LinearRegression()
    pipeline = Pipeline(steps=[("preprocessor", preprocessor), ("model", model)])
    pipeline.fit(X_train, y_train)

    y_pred_test = pipeline.predict(X_test)
    mae = float(mean_absolute_error(y_test, y_pred_test))
    rmse = float(np.sqrt(mean_squared_error(y_test, y_pred_test)))
    r2 = float(r2_score(y_test, y_pred_test))

    full_pred = pipeline.predict(df[feature_cols])
    pred_df = df[["datetime"]].copy()
    pred_df["temp_calefaccion_lineal"] = full_pred
    pred_df = pred_df.groupby("datetime", as_index=False)["temp_calefaccion_lineal"].mean()
    pred_df.to_csv(PREDICTIONS_FILE, index=False)

    if "temp_calefaccion_lineal" in gold.columns:
        gold = gold.drop(columns=["temp_calefaccion_lineal"])
    gold = gold.merge(pred_df, on="datetime", how="left")
    gold["temp_calefaccion_lineal"] = pd.to_numeric(gold.get("temp_calefaccion_lineal"), errors="coerce")
    gold.to_csv(GOLD_ENRICHED_FILE, index=False)

    payload = {"pipeline": pipeline, "feature_cols": feature_cols, "target": "temp_calefaccion_real"}
    joblib.dump(payload, MODEL_FILE)

    METRICS_FILE.write_text(
        "\n".join(
            [
                "MODELO LINEAL - TEMPERATURA CALEFACCION",
                f"Filas train: {len(train_df)}",
                f"Filas test: {len(test_df)}",
                f"Features: {', '.join(feature_cols)}",
                "",
                "Metricas test temporal 80/20:",
                f"- MAE: {mae:.4f}",
                f"- RMSE: {rmse:.4f}",
                f"- R2: {r2:.4f}",
                "",
                f"Predicciones: {PREDICTIONS_FILE}",
                f"Gold actualizado: {GOLD_ENRICHED_FILE}",
                f"Modelo guardado: {MODEL_FILE}",
            ]
        ),
        encoding="utf-8",
    )

    print(f"OK modelo lineal. MAE={mae:.4f} RMSE={rmse:.4f} R2={r2:.4f}")


if __name__ == "__main__":
    main()
