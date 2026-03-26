#!/usr/bin/env python3
"""
Exporta el dataset final de IA desde master_dataset.csv.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "gold" / "master_dataset.csv"
OUT_FILE = BASE_DIR / "data" / "gold" / "dataset_final_ia.csv"


def main() -> None:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")

    df = pd.read_csv(MASTER_FILE)
    required_cols = [
        "hora_sin",
        "hora_cos",
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

    out = df[required_cols].copy()
    # Evita arrastrar la ultima fila sin target por el shift(-1).
    out = out.dropna(subset=["target_derroche_next_hour"])
    out["target_derroche_next_hour"] = (
        out["target_derroche_next_hour"]
        .map({True: 1, False: 0, "True": 1, "False": 0, "1": 1, "0": 0})
        .fillna(0)
        .astype(int)
    )
    out = out.dropna()
    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_FILE, index=False)
    print(f"OK export IA: {OUT_FILE} filas={len(out)}")


if __name__ == "__main__":
    main()
