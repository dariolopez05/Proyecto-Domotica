"""
Normas de calefaccion por tramos horarios (Lun-Vie) con histéresis.
Temperatura de referencia: export History (bronze) o columna explicita.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


def find_col(columns: list[str], includes: list[str]) -> str:
    lowered = {c.lower(): c for c in columns}
    for col_lower, original in lowered.items():
        if all(token in col_lower for token in includes):
            return original
    raise ValueError(f"No se encontro columna con tokens: {includes}")


def build_history_datetime(history: pd.DataFrame) -> pd.Series:
    date_col = find_col(history.columns.tolist(), ["date"])
    time_col = find_col(history.columns.tolist(), ["time"])
    return pd.to_datetime(
        history[date_col].astype(str) + " " + history[time_col].astype(str),
        format="%Y.%m.%d %H:%M",
        errors="coerce",
    )


def row_thresholds_weekday(dow: int, minutes: int) -> tuple[bool, float | None, float | None]:
    """
    Lun-Vie (dow 0-4). Tramos (minutos desde medianoche):
    07:06-11:00 -> apagar >22.0, encender <21.9
    11:01-16:00 -> apagar >21.0, encender <20.9
    16:01-18:00 -> apagar >21.6, encender <21.5
    18:01-20:40 -> apagar >22.0, encender <21.9
    """
    if dow > 4:
        return False, None, None
    m = minutes
    if 426 <= m <= 660:  # 07:06 - 11:00
        return True, 22.0, 21.9
    if 661 <= m <= 960:  # 11:01 - 16:00
        return True, 21.0, 20.9
    if 961 <= m <= 1080:  # 16:01 - 18:00
        return True, 21.6, 21.5
    if 1081 <= m <= 1240:  # 18:01 - 20:40
        return True, 22.0, 21.9
    return False, None, None


def calefaccion_on_state_machine(dt: pd.Series, temp: pd.Series) -> pd.Series:
    """
    Estado encendido/apagado con histéresis; fuera de tramo o fin de semana -> 0.
    Si temp es NaN dentro de tramo, se mantiene el estado previo (como el script legacy).
    """
    dt = pd.to_datetime(dt, errors="coerce")
    dow = dt.dt.weekday.astype("int64")
    minutes = (dt.dt.hour * 60 + dt.dt.minute).astype("int64")
    tempv = pd.to_numeric(temp, errors="coerce")

    values: list[int] = []
    state = 0
    prev_date: object = None

    for i in range(len(dt)):
        cur_dt = dt.iloc[i]
        if pd.isna(cur_dt):
            state = 0
            values.append(0)
            continue
        cur_date = cur_dt.date()
        if prev_date is not None and cur_date != prev_date:
            state = 0
        prev_date = cur_date

        d = int(dow.iloc[i])
        mins = int(minutes.iloc[i])
        in_sched, t_off, t_on = row_thresholds_weekday(d, mins)

        if not in_sched:
            state = 0
            values.append(0)
            continue

        assert t_off is not None and t_on is not None
        t = tempv.iloc[i]
        if pd.isna(t):
            values.append(state)
            continue
        if t > t_off:
            state = 0
        elif t < t_on:
            state = 1
        values.append(state)

    return pd.Series(values, index=dt.index, dtype="int8")


def merge_bronze_history_temperature(df: pd.DataFrame, history_path: Path) -> pd.DataFrame:
    """
    Anade `temperatura_history_calef` desde el CSV bronze History (merge por datetime horario).
    """
    out = df.copy()
    if not history_path.exists():
        out["temperatura_history_calef"] = np.nan
        return out

    history = pd.read_csv(history_path)
    temp_col = find_col(history.columns.tolist(), ["temperature"])
    history = history.copy()
    history["datetime"] = build_history_datetime(history)
    history[temp_col] = pd.to_numeric(history[temp_col], errors="coerce")
    hist_min = history[["datetime", temp_col]].dropna(subset=["datetime"])
    hist_min = hist_min.groupby("datetime", as_index=False)[temp_col].mean()
    hist_min = hist_min.rename(columns={temp_col: "temperatura_history_calef"})

    out["datetime"] = pd.to_datetime(out["datetime"], utc=True, errors="coerce").dt.tz_localize(None)
    out = out.merge(hist_min, on="datetime", how="left")
    return out
