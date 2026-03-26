#!/usr/bin/env python3
"""
Une las predicciones del modelo de temperatura history con `master_query_result.csv`
añadiendo una columna nueva basada en la clave `datetime`.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
import pandas as pd
import psycopg2


BASE_DIR = Path(__file__).resolve().parent.parent
MASTER_FILE = BASE_DIR / "data" / "gold" / "master_query_result.csv"
PREDICTIONS_FILE = BASE_DIR / "data" / "gold" / "history_temperature_predictions.csv"
OUT_FILE = BASE_DIR / "data" / "gold" / "master_query_result_with_temperature_history_pred.csv"

ENV_FILE = BASE_DIR / ".env"


VENTILATION_PERCENT_QUERY = r"""
WITH eventos AS (
    SELECT
        time,
        entity_id,
        state,
        attributes,
        LEAD(time) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_time,
        LEAD(state) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_state
    FROM ltss
    WHERE entity_id IN (
        'binary_sensor.sensor_puerta_1_contact',
        'binary_sensor.sensor_ventana_1_contact',
        'binary_sensor.sensor_ventana_2_contact',
        'binary_sensor.sensor_ventana_3_contact',
        'binary_sensor.sensor_ventana_4_contact',
        'binary_sensor.sensor_ventana_5_contact',
        'binary_sensor.sensor_ventana_6_contact',
        'binary_sensor.sensor_ventana_7_contact',
        'binary_sensor.sensor_ventana_8_contact',
        'binary_sensor.sensor_ventana_9_contact',
        'binary_sensor.sensor_ventana_10_contact',
        'binary_sensor.sensor_ventana_12_contact'
    )
    AND state <> 'unavailable'
),
intervalos AS (
    SELECT
        entity_id,
        attributes,
        time AS inicio,
        next_time AS fin
    FROM eventos
    WHERE state = 'on'
      AND next_state = 'off'
      AND next_time IS NOT NULL
),
horas AS (
    SELECT
        entity_id,
        attributes,
        generate_series(
            date_trunc('hour', inicio),
            date_trunc('hour', fin),
            interval '1 hour'
        ) AS hora,
        inicio,
        fin
    FROM intervalos
),
duracion_hora AS (
    SELECT
        hora,
        entity_id,
        attributes,
        CASE
            WHEN entity_id = 'binary_sensor.sensor_puerta_1_contact' THEN 4
            WHEN (substring(entity_id from 'ventana_([0-9]+)')::int % 2) <> 0 THEN 2
            ELSE 1
        END AS peso,
        EXTRACT(
            EPOCH FROM
            LEAST(fin, hora + interval '1 hour')
            -
            GREATEST(inicio, hora)
        ) AS segundos_abierto
    FROM horas
)
SELECT
    hora,
    SUM(segundos_abierto * peso) AS total_ventilacion_ponderada_hora,
    ROUND(
        (SUM(segundos_abierto * peso) / (20.0 * 3600.0)) * 100,
        2
    ) AS porcentaje_ventilacion_aula
FROM duracion_hora
WHERE segundos_abierto > 0
GROUP BY hora
ORDER BY hora;
"""


def _load_dotenv_if_present() -> None:
    if ENV_FILE.exists():
        from dotenv import load_dotenv

        load_dotenv(ENV_FILE)


def fetch_ventilation_percent() -> pd.DataFrame:
    """
    Devuelve un dataframe con columnas:
      - datetime (por hora)
      - total_ventilacion_ponderada_hora (segundos ponderados)
      - porcentaje_ventilacion_aula
    """
    _load_dotenv_if_present()

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "homeassistant")
    db_user = os.getenv("DB_USER", "postgres")
    db_password = os.getenv("DB_PASSWORD", "")

    conn = psycopg2.connect(
        host=db_host,
        port=db_port,
        database=db_name,
        user=db_user,
        password=db_password,
    )
    try:
        df = pd.read_sql_query(VENTILATION_PERCENT_QUERY, conn)
    finally:
        conn.close()

    if "hora" not in df.columns:
        raise ValueError(f"La query no devolvió la columna `hora`. Columnas: {df.columns.tolist()}")

    df["datetime"] = pd.to_datetime(df["hora"], utc=True, errors="coerce")
    # Si ya viene sin tz, el utc=True no lo hace tz-aware; lo normalizamos por seguridad.
    if getattr(df["datetime"].dtype, "tz", None) is not None:
        df["datetime"] = df["datetime"].dt.tz_localize(None)
    else:
        df["datetime"] = df["datetime"]

    df["porcentaje_ventilacion_aula"] = pd.to_numeric(
        df.get("porcentaje_ventilacion_aula"), errors="coerce"
    )
    df["total_ventilacion_ponderada_hora"] = pd.to_numeric(
        df.get("total_ventilacion_ponderada_hora"), errors="coerce"
    )

    return df[
        ["datetime", "total_ventilacion_ponderada_hora", "porcentaje_ventilacion_aula"]
    ].dropna(subset=["datetime"])


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Añade al master la predicción de temperatura history y una columna "
            "binaria de calefacción calculada desde la temperatura inferida."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["fixed", "schedule"],
        default="schedule",
        help="Modo de cálculo de calefacción: fixed (umbral único) o schedule (tramos + histéresis).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=24.0,
        help="(fixed) Umbral fijo (°C). calefaccion_on_pred=1 si temperatura_history_pred < threshold.",
    )
    parser.add_argument(
        "--max-outdoor-temp",
        type=float,
        default=999.0,
        help=(
            "Si `temperatura_exterior` está disponible, solo permite ON cuando "
            "temperatura_exterior <= este valor. Usa un valor muy alto (p.ej. 999) para desactivar."
        ),
    )
    parser.add_argument(
        "--add-ventilation",
        action="store_true",
        help="Si se activa, añade `porcentaje_ventilacion_aula` consultando PostgreSQL.",
    )
    args = parser.parse_args()

    if not MASTER_FILE.exists():
        raise FileNotFoundError(f"No existe {MASTER_FILE}")
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"No existe {PREDICTIONS_FILE}")

    master = pd.read_csv(MASTER_FILE)
    preds = pd.read_csv(PREDICTIONS_FILE)

    if "datetime" not in master.columns:
        raise ValueError(f"`datetime` no está en {MASTER_FILE.name}. Columnas: {master.columns.tolist()}")
    if "datetime" not in preds.columns:
        raise ValueError(
            f"`datetime` no está en {PREDICTIONS_FILE.name}. Columnas: {preds.columns.tolist()}"
        )
    if "temperature_pred" not in preds.columns:
        raise ValueError(
            f"`temperature_pred` no está en {PREDICTIONS_FILE.name}. Columnas: {preds.columns.tolist()}"
        )

    master["datetime"] = pd.to_datetime(master["datetime"], errors="coerce")
    preds["datetime"] = pd.to_datetime(preds["datetime"], errors="coerce")

    # Aseguramos 1 predicción por timestamp (por si hubiera duplicados en el CSV).
    pred_col = "temperatura_history_pred"
    preds_subset = (
        preds.groupby("datetime", as_index=False)["temperature_pred"]
        .mean()
        .rename(columns={"temperature_pred": pred_col})
    )

    master_with_pred = master.merge(preds_subset, on="datetime", how="left")
    # Filtro exterior opcional (se aplica en ambos modos).
    if "temperatura_exterior" in master_with_pred.columns:
        outdoor = pd.to_numeric(master_with_pred["temperatura_exterior"], errors="coerce")
        outdoor_ok = outdoor.le(float(args.max_outdoor_temp)) | outdoor.isna()
    else:
        outdoor_ok = True

    # Convertimos a numérico por seguridad.
    master_with_pred[pred_col] = pd.to_numeric(master_with_pred[pred_col], errors="coerce")

    if args.mode == "fixed":
        below_threshold = master_with_pred[pred_col].lt(float(args.threshold))
        master_with_pred["calefaccion_on_pred"] = (
            (outdoor_ok & below_threshold).fillna(False).astype("int8")
        )
    else:
        # schedule (según la captura): Lunes a Viernes, con histéresis por tramo
        # 06:59-11:00  apagar si T > 22.0, encender si T < 21.9
        # 11:02-16:00  apagar si T > 22.0, encender si T < 21.9
        # 16:02-18:00  apagar si T > 21.6, encender si T < 21.5
        # 18:02-20:40  apagar si T > 22.0, encender si T < 21.9

        df = master_with_pred.sort_values("datetime").copy()
        dt = pd.to_datetime(df["datetime"], errors="coerce")
        dow = dt.dt.weekday  # 0=Lun .. 6=Dom
        minutes = dt.dt.hour * 60 + dt.dt.minute

        def in_range(start_hm: tuple[int, int], end_hm: tuple[int, int]) -> pd.Series:
            start = start_hm[0] * 60 + start_hm[1]
            end = end_hm[0] * 60 + end_hm[1]
            return minutes.ge(start) & minutes.le(end)

        # Máscaras de tramos (incluyentes en extremos).
        slot1 = (dow.le(4)) & in_range((6, 59), (11, 0))
        slot2 = (dow.le(4)) & in_range((11, 2), (16, 0))
        slot3 = (dow.le(4)) & in_range((16, 2), (18, 0))
        slot4 = (dow.le(4)) & in_range((18, 2), (20, 40))
        in_schedule = slot1 | slot2 | slot3 | slot4

        # Umbrales por fila según tramo.
        t_off = pd.Series(np.nan, index=df.index, dtype="float64")
        t_on = pd.Series(np.nan, index=df.index, dtype="float64")
        t_off.loc[slot1 | slot2 | slot4] = 22.0
        t_on.loc[slot1 | slot2 | slot4] = 21.9
        t_off.loc[slot3] = 21.6
        t_on.loc[slot3] = 21.5

        temp = df[pred_col]
        state = 0
        out = []
        prev_date = None

        for idx in df.index:
            cur_dt = dt.loc[idx]
            cur_date = None if pd.isna(cur_dt) else cur_dt.date()

            # Reinicio diario (por simplicidad) y fuera de horario.
            if prev_date is not None and cur_date is not None and cur_date != prev_date:
                state = 0
            prev_date = cur_date

            if not bool(in_schedule.loc[idx]) or not bool(outdoor_ok.loc[idx]):
                state = 0
                out.append(state)
                continue

            cur_temp = temp.loc[idx]
            if pd.isna(cur_temp):
                out.append(state)
                continue

            # Histéresis: apagar / encender, si está entre medias mantiene estado.
            if cur_temp > float(t_off.loc[idx]):
                state = 0
            elif cur_temp < float(t_on.loc[idx]):
                state = 1
            out.append(state)

        df["calefaccion_on_pred"] = pd.Series(out, index=df.index, dtype="int8")
        master_with_pred = df

    if args.add_ventilation:
        vent = fetch_ventilation_percent()
        master_with_pred = master_with_pred.merge(vent, on="datetime", how="left")

    master_with_pred.to_csv(OUT_FILE, index=False)

    print(
        f"OK: {OUT_FILE} (columnas={len(master_with_pred.columns)}, filas={len(master_with_pred)}) "
        f"mode={args.mode} threshold={float(args.threshold):.2f}°C "
        f"max_outdoor_temp={float(args.max_outdoor_temp):.2f}°C"
    )


if __name__ == "__main__":
    main()

