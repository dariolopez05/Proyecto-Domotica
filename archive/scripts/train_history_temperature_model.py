#!/usr/bin/env python3
"""
Entrena un modelo para predecir temperatura del aula en el archivo History
usando variables de contexto del dataset master_query_result.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "gold" / "master_query_result.csv"
HISTORY_FILE = BASE_DIR / "data" / "bronze" / "History_2025-09-01_100-2026-03-02_1400.csv"
PREDICTIONS_FILE = BASE_DIR / "data" / "gold" / "history_temperature_predictions.csv"
METRICS_FILE = BASE_DIR / "reports" / "history_temperature_model_metrics.txt"
CONTRAST_FILE = BASE_DIR / "reports" / "history_temperature_contraste_real_vs_pred.txt"
BACKTEST_FILE = BASE_DIR / "reports" / "history_temperature_backtest_metrics.txt"
BACKTEST_PLOT_FILE = BASE_DIR / "reports" / "history_temperature_backtest_real_vs_pred.png"
MODEL_FILE = BASE_DIR / "models" / "history_temperature_model_v2.joblib"


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


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    feat = df.copy()
    feat["hour_sin"] = np.sin(2 * np.pi * feat["hour"] / 24.0)
    feat["hour_cos"] = np.cos(2 * np.pi * feat["hour"] / 24.0)
    feat["month_sin"] = np.sin(2 * np.pi * feat["month"] / 12.0)
    feat["month_cos"] = np.cos(2 * np.pi * feat["month"] / 12.0)
    # Inercia en humedad (sin usar temperatura historica para evitar leakage del target).
    feat = feat.sort_values("datetime")
    feat["hum_lag_1h"] = feat["humidity_history"].shift(1)
    feat["hum_lag_24h"] = feat["humidity_history"].shift(24)
    return feat


def eval_metrics(y_true: pd.Series, y_pred: pd.Series) -> dict[str, float]:
    return {
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "r2": float(r2_score(y_true, y_pred)),
    }


def main() -> None:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")
    if not HISTORY_FILE.exists():
        raise FileNotFoundError(f"No existe {HISTORY_FILE}")

    reports_dir = METRICS_FILE.parent
    reports_dir.mkdir(parents=True, exist_ok=True)
    PREDICTIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
    MODEL_FILE.parent.mkdir(parents=True, exist_ok=True)

    master = pd.read_csv(MASTER_FILE)
    history = pd.read_csv(HISTORY_FILE)

    master["datetime"] = pd.to_datetime(master["datetime"], errors="coerce")
    history["datetime"] = build_history_datetime(history)

    temp_col = find_col(history.columns.tolist(), ["temperature"])
    humidity_col = find_col(history.columns.tolist(), ["humidity"])

    history = history.rename(
        columns={
            temp_col: "temperature_history",
            humidity_col: "humidity_history",
        }
    )
    history["temperature_history"] = pd.to_numeric(history["temperature_history"], errors="coerce")
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
        "humedad_aula",
        "forecast",
    ]
    available_master_features = [c for c in master_features if c in master.columns]
    master_subset = master[available_master_features].copy()

    merged = history.merge(master_subset, on="datetime", how="left")
    numeric_candidates = [
        "temperatura_exterior",
        "humedad_exterior",
        "presion",
        "nubosidad",
        "viento",
        "direccion_viento",
        "azimuth_sol",
        "elevacion_sol",
        "humedad_aula",
    ]
    for col in numeric_candidates:
        if col in merged.columns:
            merged[col] = pd.to_numeric(merged[col], errors="coerce")
    merged["hour"] = merged["datetime"].dt.hour.astype("float")
    merged["month"] = merged["datetime"].dt.month.astype("float")
    merged = build_features(merged)

    # Variables explicativas elegidas (sin usar temperatura_history como feature):
    # - Contexto temporal (hora/mes + senos/cosenos)
    # - Humedad medida en history
    # - Variables meteorologicas y solares del master
    feature_cols = [
        "hour",
        "month",
        "hour_sin",
        "hour_cos",
        "month_sin",
        "month_cos",
        "humidity_history",
        "hum_lag_1h",
        "hum_lag_24h",
        "temperatura_exterior",
        "humedad_exterior",
        "presion",
        "nubosidad",
        "viento",
        "direccion_viento",
        "azimuth_sol",
        "elevacion_sol",
        "humedad_aula",
        "dia_semana",
        "mes",
        "forecast",
    ]
    feature_cols = [c for c in feature_cols if c in merged.columns]

    model_data = merged.dropna(subset=["temperature_history", "datetime"]).copy()
    model_data = model_data.sort_values("datetime")
    if len(model_data) < 200:
        raise RuntimeError("Muy pocos datos para entrenar el modelo (<200 filas).")

    split_idx = int(len(model_data) * 0.8)
    train_df = model_data.iloc[:split_idx].copy()
    test_df = model_data.iloc[split_idx:].copy()

    X_train = train_df[feature_cols]
    y_train = train_df["temperature_history"]
    X_test = test_df[feature_cols]
    y_test = test_df["temperature_history"]

    numeric_features = X_train.select_dtypes(include=[np.number]).columns.tolist()
    categorical_features = [c for c in feature_cols if c not in numeric_features]

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
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

    model = RandomForestRegressor(
        n_estimators=400,
        max_depth=16,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1,
    )

    pipeline = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("model", model),
        ]
    )

    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)

    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    # Baseline constante: media de train (sin usar temperatura historica de test).
    baseline_pred = np.full(shape=len(y_test), fill_value=float(y_train.mean()))
    baseline_mae = mean_absolute_error(y_test, baseline_pred)
    baseline_rmse = np.sqrt(mean_squared_error(y_test, baseline_pred))
    baseline_r2 = r2_score(y_test, baseline_pred)
    best_model_name = "random_forest"

    full_X = merged[feature_cols]
    merged["pred_random_forest"] = pipeline.predict(full_X)
    merged["temperature_pred"] = merged["pred_random_forest"]
    model_payload = {
        "model_type": "random_forest",
        "pipeline": pipeline,
        "feature_cols": feature_cols,
        "note": "No usa temperatura_history como variable de entrada.",
    }

    merged["error_abs"] = (merged["temperature_history"] - merged["temperature_pred"]).abs()
    merged.to_csv(PREDICTIONS_FILE, index=False)
    joblib.dump(model_payload, MODEL_FILE)

    # Contraste global (informativo): puede ser optimista por usar lags reales.
    contrast_df = merged.dropna(subset=["temperature_history", "temperature_pred"]).copy()
    contrast_metrics = eval_metrics(contrast_df["temperature_history"], contrast_df["temperature_pred"])
    contrast_bias = float((contrast_df["temperature_pred"] - contrast_df["temperature_history"]).mean())
    contrast_mape = float(
        (
            (contrast_df["temperature_history"] - contrast_df["temperature_pred"]).abs()
            / contrast_df["temperature_history"].abs().clip(lower=1e-6)
        ).mean()
        * 100
    )
    contrast_corr = float(contrast_df["temperature_history"].corr(contrast_df["temperature_pred"]))

    contrast_text = "\n".join(
        [
            "CONTRASTE GLOBAL REAL VS PREDICHA (INFORMATIVO)",
            "Nota: este contraste puede ser optimista.",
            f"Filas evaluadas: {len(contrast_df)}",
            f"Modelo usado para prediccion final: {best_model_name}",
            "",
            f"- MAE: {contrast_metrics['mae']:.4f}",
            f"- RMSE: {contrast_metrics['rmse']:.4f}",
            f"- R2: {contrast_metrics['r2']:.4f}",
            f"- MAPE: {contrast_mape:.2f}%",
            f"- Bias medio (pred-real): {contrast_bias:.4f}",
            f"- Correlacion Pearson: {contrast_corr:.4f}",
            "",
            f"Fuente de predicciones: {PREDICTIONS_FILE}",
        ]
    )
    CONTRAST_FILE.write_text(contrast_text, encoding="utf-8")

    # Backtesting fuera de muestra (sin fuga): solo tramo test temporal.
    backtest_df = merged.iloc[split_idx:].dropna(subset=["temperature_history", "datetime"]).copy()
    backtest_df["temperature_pred_backtest"] = np.nan
    if best_model_name == "naive_lag_1h":
        backtest_df["temperature_pred_backtest"] = backtest_df["temp_lag_1h"]
    else:
        backtest_df["temperature_pred_backtest"] = pipeline.predict(backtest_df[feature_cols])

    backtest_df = backtest_df.dropna(subset=["temperature_pred_backtest"]).copy()
    backtest_metrics = eval_metrics(backtest_df["temperature_history"], backtest_df["temperature_pred_backtest"])
    backtest_bias = float(
        (backtest_df["temperature_pred_backtest"] - backtest_df["temperature_history"]).mean()
    )
    backtest_mape = float(
        (
            (backtest_df["temperature_history"] - backtest_df["temperature_pred_backtest"]).abs()
            / backtest_df["temperature_history"].abs().clip(lower=1e-6)
        ).mean()
        * 100
    )
    backtest_corr = float(
        backtest_df["temperature_history"].corr(backtest_df["temperature_pred_backtest"])
    )

    backtest_text = "\n".join(
        [
            "BACKTEST FUERA DE MUESTRA (TEMPORAL HOLDOUT)",
            "Este reporte es el valido para detectar sobreajuste y leakage.",
            f"Filas evaluadas (test): {len(backtest_df)}",
            f"Modelo evaluado: {best_model_name}",
            "",
            f"- MAE: {backtest_metrics['mae']:.4f}",
            f"- RMSE: {backtest_metrics['rmse']:.4f}",
            f"- R2: {backtest_metrics['r2']:.4f}",
            f"- MAPE: {backtest_mape:.2f}%",
            f"- Bias medio (pred-real): {backtest_bias:.4f}",
            f"- Correlacion Pearson: {backtest_corr:.4f}",
        ]
    )
    BACKTEST_FILE.write_text(backtest_text, encoding="utf-8")

    plt.figure(figsize=(16, 6))
    plt.plot(backtest_df["datetime"], backtest_df["temperature_history"], label="Real", linewidth=1.2)
    plt.plot(
        backtest_df["datetime"],
        backtest_df["temperature_pred_backtest"],
        label="Predicha (backtest)",
        linewidth=1.0,
        alpha=0.85,
    )
    plt.title("Backtest temporal: temperatura real vs predicha")
    plt.xlabel("Fecha")
    plt.ylabel("Temperatura (C)")
    plt.legend()
    plt.grid(alpha=0.25)
    plt.tight_layout()
    plt.savefig(BACKTEST_PLOT_FILE, dpi=180)
    plt.close()

    improvement_mae = (1.0 - (mae / baseline_mae)) * 100 if baseline_mae > 0 else np.nan
    improvement_rmse = (1.0 - (rmse / baseline_rmse)) * 100 if baseline_rmse > 0 else np.nan

    metrics_text = "\n".join(
        [
            "MODELO: RandomForestRegressor",
            f"Filas training: {len(train_df)}",
            f"Filas test: {len(test_df)}",
            f"Variables usadas: {', '.join(feature_cols)}",
            "",
            "METRICAS (validacion temporal 80/20):",
            f"- MAE: {mae:.4f}",
            f"- RMSE: {rmse:.4f}",
            f"- R2: {r2:.4f}",
            "",
            "BASELINE CONSTANTE (media de train):",
            f"- MAE baseline: {baseline_mae:.4f}",
            f"- RMSE baseline: {baseline_rmse:.4f}",
            f"- R2 baseline: {baseline_r2:.4f}",
            "",
            "MEJORA VS BASELINE:",
            f"- Mejora MAE: {improvement_mae:.2f}%",
            f"- Mejora RMSE: {improvement_rmse:.2f}%",
            "",
            f"Modelo seleccionado para produccion: {best_model_name}",
            "",
            f"Predicciones guardadas en: {PREDICTIONS_FILE}",
            f"Modelo guardado en: {MODEL_FILE}",
            f"Reporte de contraste guardado en: {CONTRAST_FILE}",
            f"Reporte de backtest guardado en: {BACKTEST_FILE}",
            f"Grafica de backtest guardada en: {BACKTEST_PLOT_FILE}",
        ]
    )

    METRICS_FILE.write_text(metrics_text, encoding="utf-8")

    print(metrics_text)


if __name__ == "__main__":
    main()
