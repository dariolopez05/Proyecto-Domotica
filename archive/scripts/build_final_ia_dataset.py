#!/usr/bin/env python3
"""
Construye target de derroche y dataset final para IA.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
GOLD_FILE = BASE_DIR / "data" / "gold" / "master_query_result_with_temperature_history_pred.csv"
OUT_FILE = BASE_DIR / "data" / "gold" / "dataset_final_ia.csv"


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera derroche/target y CSV final IA.")
    parser.add_argument(
        "--ventilation-threshold",
        type=float,
        default=15.0,
        help="Umbral de porcentaje de ventilacion para considerar derroche.",
    )
    args = parser.parse_args()

    if not GOLD_FILE.exists():
        raise FileNotFoundError(f"No existe {GOLD_FILE}")

    df = pd.read_csv(GOLD_FILE)
    df["datetime"] = pd.to_datetime(df.get("datetime"), errors="coerce")
    df["hora"] = pd.to_numeric(df.get("hora"), errors="coerce")

    for col in [
        "temperatura_aula",
        "temperatura_exterior",
        "humedad_aula",
        "viento",
        "nubosidad",
        "elevacion_sol",
        "porcentaje_ventilacion_aula",
    ]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "calefaccion_on_pred" not in df.columns:
        raise ValueError("Falta `calefaccion_on_pred` en el gold.")
    if "porcentaje_ventilacion_aula" not in df.columns:
        raise ValueError("Falta `porcentaje_ventilacion_aula` en el gold.")

    heat_on = pd.to_numeric(df["calefaccion_on_pred"], errors="coerce").fillna(0).astype(int).eq(1)
    vent_high = df["porcentaje_ventilacion_aula"].gt(float(args.ventilation_threshold))

    df["derroche"] = (heat_on & vent_high)
    df["target_derroche_next_hour"] = df["derroche"].shift(-1)

    # Features ciclicas de hora.
    df["hora_sin"] = np.sin(2 * np.pi * df["hora"] / 24.0)
    df["hora_cos"] = np.cos(2 * np.pi * df["hora"] / 24.0)

    # Guardamos tambien las nuevas columnas en el gold enriquecido para trazabilidad.
    df.to_csv(GOLD_FILE, index=False)

    final_df = pd.DataFrame(
        {
            "hora_sin": df["hora_sin"],
            "hora_cos": df["hora_cos"],
            "temp_aula": df.get("temperatura_aula"),
            "temp_ext": df.get("temperatura_exterior"),
            "humedad_aula": df.get("humedad_aula"),
            "viento": df.get("viento"),
            "nubosidad": df.get("nubosidad"),
            "sol_elevacion": df.get("elevacion_sol"),
            "porcentaje_ventilacion_aula": df.get("porcentaje_ventilacion_aula"),
            "target_derroche_next_hour": df["target_derroche_next_hour"],
        }
    )

    final_df = final_df.dropna(subset=["target_derroche_next_hour"]).copy()
    final_df["target_derroche_next_hour"] = final_df["target_derroche_next_hour"].astype(bool).astype("int8")
    final_df = final_df.dropna()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(OUT_FILE, index=False)

    print(
        f"OK dataset IA: {OUT_FILE} filas={len(final_df)} "
        f"umbral_ventilacion={float(args.ventilation_threshold):.2f}%"
    )


if __name__ == "__main__":
    main()
