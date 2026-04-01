#!/usr/bin/env python3
"""
Web app para predicción de derroche energético (siguiente hora).
Ejecutar: python web_app/app.py
Abre http://localhost:5000 en el navegador.
"""

from __future__ import annotations

import math
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent.parent
KERAS_MODEL_FILE = BASE_DIR / "models" / "nn_derroche_model_keras.keras"
KERAS_PREPROCESS_FILE = BASE_DIR / "models" / "nn_derroche_preprocess_keras.joblib"

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Carga del modelo al arrancar (una sola vez)
# ---------------------------------------------------------------------------
_model = None
_pre = None


def _load_assets():
    global _model, _pre
    if _pre is None:
        _pre = joblib.load(KERAS_PREPROCESS_FILE)
    if _model is None:
        import tensorflow as tf
        _model = tf.keras.models.load_model(KERAS_MODEL_FILE)


# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:
        _load_assets()
        data = request.get_json(force=True)

        hora = int(data["hora"])
        hora_sin = math.sin(2 * math.pi * hora / 24)
        hora_cos = math.cos(2 * math.pi * hora / 24)

        row = {
            "hora_sin": hora_sin,
            "hora_cos": hora_cos,
            "temp_aula": float(data["temp_aula"]),
            "temp_ext": float(data["temp_ext"]),
            "humedad_aula": float(data["humedad_aula"]),
            "viento": float(data["viento"]),
            "nubosidad": float(data["nubosidad"]),
            "sol_elevacion": float(data["sol_elevacion"]),
            "porcentaje_ventilacion_aula": float(data["porcentaje_ventilacion_aula"]),
        }

        imputer = _pre["imputer"]
        scaler = _pre["scaler"]
        features = _pre["features"]
        threshold = float(_pre.get("threshold", 0.5))

        X_df = pd.DataFrame([row])[features]
        X_imp = imputer.transform(X_df.to_numpy())
        X_scaled = scaler.transform(X_imp)

        proba = float(_model.predict(X_scaled, verbose=0).reshape(-1)[0])
        pred = int(proba >= threshold)

        return jsonify({
            "ok": True,
            "prediction": pred,
            "probability": round(proba * 100, 2),
            "threshold": round(threshold * 100, 2),
            "hora_sin": round(hora_sin, 4),
            "hora_cos": round(hora_cos, 4),
        })

    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Cargando modelo...")
    _load_assets()
    print("Modelo cargado. Abre http://localhost:5000")
    app.run(debug=False, port=5000)
