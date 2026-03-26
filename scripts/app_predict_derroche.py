#!/usr/bin/env python3
"""
App CLI minima para introducir variables y predecir derroche en la siguiente hora.
Uso:
python scripts/app_predict_derroche.py --hora-sin ... --hora-cos ... --temp-aula ...
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
KERAS_MODEL_FILE = BASE_DIR / "models" / "nn_derroche_model_keras.keras"
KERAS_PREPROCESS_FILE = BASE_DIR / "models" / "nn_derroche_preprocess_keras.joblib"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prediccion de derroche siguiente hora (0/1).")
    parser.add_argument("--hora-sin", type=float, required=True)
    parser.add_argument("--hora-cos", type=float, required=True)
    parser.add_argument("--temp-aula", type=float, required=True)
    parser.add_argument("--temp-ext", type=float, required=True)
    parser.add_argument("--humedad-aula", type=float, required=True)
    parser.add_argument("--viento", type=float, required=True)
    parser.add_argument("--nubosidad", type=float, required=True)
    parser.add_argument("--sol-elevacion", type=float, required=True)
    parser.add_argument("--porcentaje-ventilacion-aula", type=float, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not KERAS_MODEL_FILE.exists() or not KERAS_PREPROCESS_FILE.exists():
        raise FileNotFoundError(
            "No existe el modelo Keras o el preprocesado.\n"
            f"- Modelo: {KERAS_MODEL_FILE}\n"
            f"- Prepro: {KERAS_PREPROCESS_FILE}\n"
            "Ejecuta antes scripts/train_nn_derroche_model_keras.py"
        )

    pre = joblib.load(KERAS_PREPROCESS_FILE)
    imputer = pre["imputer"]
    scaler = pre["scaler"]
    features = pre["features"]
    threshold = float(pre.get("threshold", 0.5))

    import tensorflow as tf

    row = {
        "hora_sin": args.hora_sin,
        "hora_cos": args.hora_cos,
        "temp_aula": args.temp_aula,
        "temp_ext": args.temp_ext,
        "humedad_aula": args.humedad_aula,
        "viento": args.viento,
        "nubosidad": args.nubosidad,
        "sol_elevacion": args.sol_elevacion,
        "porcentaje_ventilacion_aula": args.porcentaje_ventilacion_aula,
    }
    X_df = pd.DataFrame([row])[features]
    X_imp = imputer.transform(X_df.to_numpy())
    X_scaled = scaler.transform(X_imp)

    model = tf.keras.models.load_model(KERAS_MODEL_FILE)
    proba = float(model.predict(X_scaled, verbose=0).reshape(-1)[0])
    pred = int(proba >= threshold)

    print(f"Prediccion derroche siguiente hora (0/1): {pred}")
    print(f"Probabilidad derroche siguiente hora: {proba:.4f}")
    print(f"Umbral usado: {threshold:.2f}")


if __name__ == "__main__":
    main()
