#!/usr/bin/env python3
"""
Construye la capa Silver (Medallion): tabla maestra horaria desde SQL + reglas.
Salida: data/silver/master_dataset.csv
"""

from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from utils.db_manager import query_to_dataframe
from utils.config import (
    BRONZE_HISTORY_CSV,
    DOOR_WEIGHT,
    MASTER_DATASET_CSV,
    TOTAL_WEIGHT_DIVISOR,
    WINDOW_WEIGHT_LARGE,
    WINDOW_WEIGHT_SMALL,
)
from utils.heating_normas import calefaccion_on_state_machine, merge_bronze_history_temperature
from utils.preprocessing import add_derroche_targets, add_temporal_cyclical_features, add_weighted_ventilation_pct

QUERY_FILE = BASE_DIR / "queries" / "master_query.sql"
OUT_FILE = MASTER_DATASET_CSV
# Fallback si no hay DB: silver previo, layout antiguo en gold, o CSV legacy
FALLBACK_FILES = [
    MASTER_DATASET_CSV,
    BASE_DIR / "data" / "gold" / "master_dataset.csv",
    BASE_DIR / "data" / "gold" / "master_query_result_with_temperature_history_pred.csv",
    BASE_DIR / "data" / "gold" / "master_query_result.csv",
]


def add_calendar_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["datetime"] = pd.to_datetime(out["datetime"], utc=True, errors="coerce").dt.tz_localize(None)

    dias_semana = {
        0: "Lunes",
        1: "Martes",
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo",
    }
    meses = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    out["dia_semana"] = out["datetime"].dt.dayofweek.map(dias_semana)
    out["mes"] = out["datetime"].dt.month.map(meses)
    out["hora"] = out["datetime"].dt.hour
    return out


def add_heating_state_schedule(df: pd.DataFrame) -> pd.DataFrame:
    """Misma regla horaria que normas History; temperatura = lineal si existe, si no aula."""
    out = df.sort_values("datetime").copy()
    temp_pred_col = "temp_calefaccion_lineal"
    if temp_pred_col not in out.columns:
        out[temp_pred_col] = pd.to_numeric(out.get("temperatura_aula"), errors="coerce")
    out["calefaccion_on_pred"] = calefaccion_on_state_machine(out["datetime"], out[temp_pred_col])
    return out


def main() -> None:
    if not QUERY_FILE.exists():
        raise FileNotFoundError(f"No existe {QUERY_FILE}")

    query_template = QUERY_FILE.read_text(encoding="utf-8")
    query = (
        query_template.replace("{{DOOR_WEIGHT}}", str(DOOR_WEIGHT))
        .replace("{{WINDOW_WEIGHT_LARGE}}", str(WINDOW_WEIGHT_LARGE))
        .replace("{{WINDOW_WEIGHT_SMALL}}", str(WINDOW_WEIGHT_SMALL))
        .replace("{{TOTAL_WEIGHT_DIVISOR}}", str(TOTAL_WEIGHT_DIVISOR))
    )
    try:
        df = query_to_dataframe(query)
        print("Fuente de datos: PostgreSQL (master_query.sql)")
    except Exception as exc:
        fallback_found = next((f for f in FALLBACK_FILES if f.exists()), None)
        if fallback_found is None:
            raise
        print(f"Aviso: no se pudo consultar PostgreSQL ({exc}).")
        print(f"Usando fallback local: {fallback_found}")
        df = pd.read_csv(fallback_found)
    df = add_calendar_columns(df)
    df = add_weighted_ventilation_pct(df)
    df = merge_bronze_history_temperature(df, BRONZE_HISTORY_CSV)
    df["calefaccion_on_normas_history"] = calefaccion_on_state_machine(
        df["datetime"], df["temperatura_history_calef"]
    )
    df = add_heating_state_schedule(df)
    df = add_derroche_targets(df)
    df["derroche"] = df["derroche"].astype("boolean")
    df["target_derroche_next_hour"] = (
        df["target_derroche_next_hour"].astype("boolean")
    )
    df = add_temporal_cyclical_features(df)
    # Aliases estables para IA (evita ambiguedad de nombres entre scripts).
    if "temperatura_aula" in df.columns:
        df["temp_aula"] = pd.to_numeric(df["temperatura_aula"], errors="coerce")
    if "temperatura_exterior" in df.columns:
        df["temp_ext"] = pd.to_numeric(df["temperatura_exterior"], errors="coerce")
    if "elevacion_sol" in df.columns:
        df["sol_elevacion"] = pd.to_numeric(df["elevacion_sol"], errors="coerce")

    ordered_cols = ["datetime", "dia_semana", "mes", "hora"]
    rest = [c for c in df.columns if c not in ordered_cols]
    df = df[ordered_cols + rest]

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_FILE, index=False)
    print(f"OK silver (master): {OUT_FILE} filas={len(df)} columnas={len(df.columns)}")


if __name__ == "__main__":
    main()
