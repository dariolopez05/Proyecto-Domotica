#!/usr/bin/env python3
"""
Analisis rapido de correlacion de sensores de humedad del aula.
Genera estadisticas y graficos para justificar redundancia (Tarea 3 del PDF).
"""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "silver" / "master_dataset.csv"
OUT_DIR = BASE_DIR / "reports" / "humidity_analysis"


def main() -> None:
    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")

    df = pd.read_csv(MASTER_FILE)
    df["datetime"] = pd.to_datetime(df.get("datetime"), errors="coerce")

    humidity_candidates = [
        c
        for c in df.columns
        if ("humedad" in c.lower() or "humidity" in c.lower()) and c.lower() != "porcentaje_ventilacion_aula"
    ]
    if not humidity_candidates:
        raise RuntimeError("No se han encontrado columnas de humedad en el dataset gold.")

    hum = df[["datetime"] + humidity_candidates].copy()
    for c in humidity_candidates:
        hum[c] = pd.to_numeric(hum[c], errors="coerce")
    hum = hum.dropna(how="all", subset=humidity_candidates).sort_values("datetime")

    stats = hum[humidity_candidates].describe().T
    stats["missing"] = hum[humidity_candidates].isna().sum()
    stats["missing_pct"] = (stats["missing"] / len(hum) * 100).round(2)
    stats.to_csv(OUT_DIR / "humidity_stats.csv")

    corr = hum[humidity_candidates].corr()
    corr.to_csv(OUT_DIR / "humidity_correlation_matrix.csv")

    plt.figure(figsize=(10, 8))
    sns.heatmap(corr, annot=True, cmap="coolwarm", vmin=-1, vmax=1, fmt=".3f")
    plt.title("Correlacion entre sensores/variables de humedad")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "humidity_correlation_heatmap.png", dpi=180)
    plt.close()

    plt.figure(figsize=(14, 6))
    for col in humidity_candidates:
        plt.plot(hum["datetime"], hum[col], label=col, alpha=0.8)
    plt.title("Serie temporal de humedad (variables disponibles)")
    plt.xlabel("Datetime")
    plt.ylabel("Humedad")
    plt.legend(loc="best")
    plt.tight_layout()
    plt.savefig(OUT_DIR / "humidity_timeseries.png", dpi=180)
    plt.close()

    print(f"OK analisis humedad en {OUT_DIR}")
    print(f"Columnas analizadas: {', '.join(humidity_candidates)}")


if __name__ == "__main__":
    main()
