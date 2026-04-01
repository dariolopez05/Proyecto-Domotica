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


def _is_in_heating_schedule(hora: int, dia_semana: int) -> bool:
    """Horario activo de calefaccion: Lun-Vie y franjas configuradas."""
    if dia_semana >= 5:
        return False
    t = hora * 60
    slots = [
        (7 * 60 + 6, 11 * 60),
        (11 * 60 + 1, 16 * 60),
        (16 * 60 + 1, 18 * 60),
        (18 * 60 + 1, 20 * 60 + 40),
    ]
    return any(start <= t <= end for start, end in slots)


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
        dia_semana = int(data.get("dia_semana", 0))  # 0=Lun ... 6=Dom
        mes = int(data.get("mes", 1))  # 1..12

        if not _is_in_heating_schedule(hora, dia_semana):
            return jsonify({
                "ok": False,
                "error": "Prediccion no disponible fuera del horario de calefaccion (Lun-Vie, 07:06-20:40 por franjas).",
            }), 400

        hora_sin = math.sin(2 * math.pi * hora / 24)
        hora_cos = math.cos(2 * math.pi * hora / 24)
        dia_semana_sin = math.sin(2 * math.pi * dia_semana / 7)
        dia_semana_cos = math.cos(2 * math.pi * dia_semana / 7)
        mes_sin = math.sin(2 * math.pi * (mes - 1) / 12)
        mes_cos = math.cos(2 * math.pi * (mes - 1) / 12)

        row = {
            "hora_sin": hora_sin,
            "hora_cos": hora_cos,
            "dia_semana_sin": dia_semana_sin,
            "dia_semana_cos": dia_semana_cos,
            "mes_sin": mes_sin,
            "mes_cos": mes_cos,
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
            "dia_semana_sin": round(dia_semana_sin, 4),
            "dia_semana_cos": round(dia_semana_cos, 4),
            "mes_sin": round(mes_sin, 4),
            "mes_cos": round(mes_cos, 4),
        })

    except Exception as exc:
        return jsonify({"ok": False, "error": str(exc)}), 500


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Cargando modelo...")
    _load_assets()
    print("Modelo cargado. Abre http://localhost:5000")
    app.run(debug=False, port=5000)
