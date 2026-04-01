#!/usr/bin/env python3
"""
Exporta el dataset Gold de IA desde data/silver/master_dataset.csv.

Solo filas con calefaccion encendida (1): si esta apagada (0), no sirve para
entrenar/inferir el modelo de derroche. Usa `calefaccion_on_normas_history`
si existe; si no, `calefaccion_on_pred`.

Las features pueden llevar NaN: el imputer del entrenamiento Keras (fit en train)
las rellena; no se hace dropna global aqui para no descartar filas imputables.
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.config import DATASET_FINAL_IA_CSV, MASTER_DATASET_CSV

MASTER_FILE = MASTER_DATASET_CSV
OUT_FILE = DATASET_FINAL_IA_CSV


def main() -> None:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")

    df = pd.read_csv(MASTER_FILE)
    required_cols = [
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
        "target_derroche_next_hour",
    ]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Faltan columnas en master_dataset: {missing}")

    heat_col = (
        "calefaccion_on_normas_history"
        if "calefaccion_on_normas_history" in df.columns
        else "calefaccion_on_pred"
    )
    if heat_col in df.columns:
        heat_on = pd.to_numeric(df[heat_col], errors="coerce").fillna(0).astype(int).eq(1)
        df = df.loc[heat_on].copy()

    out = df[required_cols].copy()
    # Sin target no hay supervision (p. ej. ultima fila tras shift(-1)).
    out = out.dropna(subset=["target_derroche_next_hour"])
    out["target_derroche_next_hour"] = (
        out["target_derroche_next_hour"]
        .map({True: 1, False: 0, "True": 1, "False": 0, "1": 1, "0": 0})
        .fillna(0)
        .astype(int)
    )
    # Features con huecos: se dejan como NaN para SimpleImputer en train_nn_derroche_model_keras.py
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)
    print(f"OK export IA: {OUT_FILE} filas={len(out)}")


if __name__ == "__main__":
    main()
