#!/usr/bin/env python3
"""
App CLI minima para introducir variables y predecir derroche en la siguiente hora.

Contexto temporal (alineado con el dataset / PDF: hora, dia semana, mes):
  Opcion A — una fecha/hora ISO (recomendado):
    python scripts/app_predict_derroche.py --fecha "2025-12-18 16:00:00" --temp-aula ...

  Opcion B — hora + dia de semana + mes (pandas: 0=Lunes ... 6=Domingo):
    python scripts/app_predict_derroche.py --hora 16 --dia-semana 3 --mes 12 --temp-aula ...

  Opcion C — pasar senos/cosenos a mano (6 pares + features de sensores):
    --hora-sin --hora-cos --dia-semana-sin --dia-semana-cos --mes-sin --mes-cos ...
"""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
KERAS_MODEL_FILE = BASE_DIR / "models" / "nn_derroche_model_keras.keras"
KERAS_PREPROCESS_FILE = BASE_DIR / "models" / "nn_derroche_preprocess_keras.joblib"


def _hour_0_23(value: str) -> int:
    h = int(value)
    if not 0 <= h <= 23:
        raise argparse.ArgumentTypeError("hora debe estar entre 0 y 23")
    return h


def _dow_0_6(value: str) -> int:
    d = int(value)
    if not 0 <= d <= 6:
        raise argparse.ArgumentTypeError("dia-semana: 0=Lunes ... 6=Domingo (pandas dayofweek)")
    return d


def _mes_1_12(value: str) -> int:
    m = int(value)
    if not 1 <= m <= 12:
        raise argparse.ArgumentTypeError("mes debe estar entre 1 y 12")
    return m


def temporal_from_parts(hora: float, dow: float, mes: float) -> dict[str, float]:
    return {
        "hora_sin": float(np.sin(2 * np.pi * hora / 24.0)),
        "hora_cos": float(np.cos(2 * np.pi * hora / 24.0)),
        "dia_semana_sin": float(np.sin(2 * np.pi * dow / 7.0)),
        "dia_semana_cos": float(np.cos(2 * np.pi * dow / 7.0)),
        "mes_sin": float(np.sin(2 * np.pi * (mes - 1.0) / 12.0)),
        "mes_cos": float(np.cos(2 * np.pi * (mes - 1.0) / 12.0)),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prediccion de derroche siguiente hora (0/1).")
    parser.add_argument(
        "--fecha",
        type=str,
        default=None,
        metavar="ISO",
        help="Fecha y hora (ej. 2025-12-18 16:00:00); define hora, dia semana y mes ciclicos.",
    )
    parser.add_argument(
        "--hora",
        type=_hour_0_23,
        default=None,
        metavar="0-23",
        help="Hora 0-23 (junto con --dia-semana y --mes si no usas --fecha).",
    )
    parser.add_argument(
        "--dia-semana",
        type=_dow_0_6,
        default=None,
        metavar="0-6",
        help="0=Lunes ... 6=Domingo (igual que pandas datetime.dayofweek).",
    )
    parser.add_argument(
        "--mes",
        type=_mes_1_12,
        default=None,
        metavar="1-12",
        help="Mes del año 1-12.",
    )
    parser.add_argument("--hora-sin", type=float, default=None)
    parser.add_argument("--hora-cos", type=float, default=None)
    parser.add_argument("--dia-semana-sin", type=float, default=None)
    parser.add_argument("--dia-semana-cos", type=float, default=None)
    parser.add_argument("--mes-sin", type=float, default=None)
    parser.add_argument("--mes-cos", type=float, default=None)
    parser.add_argument("--temp-aula", type=float, required=True)
    parser.add_argument("--temp-ext", type=float, required=True)
    parser.add_argument("--humedad-aula", type=float, required=True)
    parser.add_argument("--viento", type=float, required=True)
    parser.add_argument("--nubosidad", type=float, required=True)
    parser.add_argument("--sol-elevacion", type=float, required=True)
    parser.add_argument("--porcentaje-ventilacion-aula", type=float, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    manual = (
        args.hora_sin is not None
        and args.hora_cos is not None
        and args.dia_semana_sin is not None
        and args.dia_semana_cos is not None
        and args.mes_sin is not None
        and args.mes_cos is not None
    )

    if args.fecha is not None:
        if manual or args.hora is not None:
            raise SystemExit("Usa solo --fecha, o --hora+--dia-semana+--mes, o los 6 senos/cosenos.")
        dt = pd.to_datetime(args.fecha)
        t = temporal_from_parts(float(dt.hour), float(dt.dayofweek), float(dt.month))
    elif manual:
        t = {
            "hora_sin": float(args.hora_sin),
            "hora_cos": float(args.hora_cos),
            "dia_semana_sin": float(args.dia_semana_sin),
            "dia_semana_cos": float(args.dia_semana_cos),
            "mes_sin": float(args.mes_sin),
            "mes_cos": float(args.mes_cos),
        }
    elif args.hora is not None and args.dia_semana is not None and args.mes is not None:
        if args.hora_sin is not None or args.hora_cos is not None:
            raise SystemExit("Con --hora/--dia-semana/--mes no uses --hora-sin/--hora-cos.")
        t = temporal_from_parts(float(args.hora), float(args.dia_semana), float(args.mes))
    else:
        raise SystemExit(
            "Indica contexto temporal: --fecha (ISO), o --hora + --dia-semana + --mes, "
            "o los seis argumentos --hora-sin/--hora-cos/--dia-semana-sin/..."
        )

    if not KERAS_MODEL_FILE.exists() or not KERAS_PREPROCESS_FILE.exists():
        raise FileNotFoundError(
            "No existe el modelo Keras o el preprocesado.\n"
            f"- Modelo: {KERAS_MODEL_FILE}\n"
            f"- Prepro: {KERAS_PREPROCESS_FILE}\n"
            "Ejecuta antes scripts/train_nn_derroche_model_keras.py"
        )

    pre = joblib.load(KERAS_PREPROCESS_FILE)
    imputer = pre["imputer"]
    scaler = pre["scaler"]
    features = pre["features"]
    threshold = float(pre.get("threshold", 0.5))

    import tensorflow as tf

    row = {
        **t,
        "temp_aula": args.temp_aula,
        "temp_ext": args.temp_ext,
        "humedad_aula": args.humedad_aula,
        "viento": args.viento,
        "nubosidad": args.nubosidad,
        "sol_elevacion": args.sol_elevacion,
        "porcentaje_ventilacion_aula": args.porcentaje_ventilacion_aula,
    }
    X_df = pd.DataFrame([row])[features]
    X_imp = imputer.transform(X_df.to_numpy())
    X_scaled = scaler.transform(X_imp)

    model = tf.keras.models.load_model(KERAS_MODEL_FILE)
    proba = float(model.predict(X_scaled, verbose=0).reshape(-1)[0])
    pred = int(proba >= threshold)

    if args.fecha is not None:
        print(f"Fecha usada: {args.fecha}")
    elif args.hora is not None and not manual:
        print(
            f"Tiempo: hora={args.hora} dia_semana={args.dia_semana} (0=Lun) mes={args.mes}"
        )
    print(f"Prediccion derroche siguiente hora (0/1): {pred}")
    print(f"Probabilidad derroche siguiente hora: {proba:.4f}")
    print(f"Umbral usado: {threshold:.2f}")


if __name__ == "__main__":
    main()
