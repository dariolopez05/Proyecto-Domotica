from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from utils.config import DERROCHE_VENTILATION_THRESHOLD_PCT


def add_weighted_ventilation_pct(df: pd.DataFrame) -> pd.DataFrame:
    if "porcentaje_ventilacion_aula" not in df.columns:
        df["porcentaje_ventilacion_aula"] = 0.0
    df["porcentaje_ventilacion_aula"] = pd.to_numeric(
        df["porcentaje_ventilacion_aula"], errors="coerce"
    ).fillna(0.0)
    return df


def scale_features(df: pd.DataFrame, feature_cols: list[str]) -> tuple[pd.DataFrame, StandardScaler]:
    """
    Escalado estandar para IA (misma filosofia del examen: normalizacion previa a red neuronal).
    """
    out = df.copy()
    scaler = StandardScaler()
    out[feature_cols] = scaler.fit_transform(out[feature_cols])
    return out, scaler


def add_derroche_targets(df: pd.DataFrame, threshold_pct: float = DERROCHE_VENTILATION_THRESHOLD_PCT) -> pd.DataFrame:
    out = df.copy()
    heat_col = (
        "calefaccion_on_normas_history"
        if "calefaccion_on_normas_history" in out.columns
        else "calefaccion_on_pred"
    )
    heat_on = pd.to_numeric(out.get(heat_col), errors="coerce").fillna(0).astype(int).eq(1)
    vent_high = pd.to_numeric(out.get("porcentaje_ventilacion_aula"), errors="coerce").fillna(0.0).gt(
        float(threshold_pct)
    )
    out["derroche"] = heat_on & vent_high
    out["target_derroche_next_hour"] = out["derroche"].shift(-1)
    return out


def add_temporal_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Codificación cíclica coherente con el PDF: hora, día de la semana y mes.
    - Hora: columna `hora` (0-23) o derivada de `datetime`.
    - Día: pandas dayofweek 0=Lunes … 6=Domingo.
    - Mes: 1-12 en ciclo anual (enero y diciembre vecinos en el círculo).
    """
    out = df.copy()
    dt = pd.to_datetime(out["datetime"], errors="coerce")
    hour = pd.to_numeric(out.get("hora"), errors="coerce")
    hour = hour.fillna(dt.dt.hour).astype(float)
    out["hora_sin"] = np.sin(2 * np.pi * hour / 24.0)
    out["hora_cos"] = np.cos(2 * np.pi * hour / 24.0)
    dow = dt.dt.dayofweek.astype(float)
    out["dia_semana_sin"] = np.sin(2 * np.pi * dow / 7.0)
    out["dia_semana_cos"] = np.cos(2 * np.pi * dow / 7.0)
    mes = dt.dt.month.astype(float)
    out["mes_sin"] = np.sin(2 * np.pi * (mes - 1.0) / 12.0)
    out["mes_cos"] = np.cos(2 * np.pi * (mes - 1.0) / 12.0)
    return out


def add_hour_cyclical_features(df: pd.DataFrame) -> pd.DataFrame:
    """Alias: incluye hora, día de semana y mes (ver `add_temporal_cyclical_features`)."""
    return add_temporal_cyclical_features(df)

