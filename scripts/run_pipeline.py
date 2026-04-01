#!/usr/bin/env python3
"""
Ejecuta el pipeline completo del proyecto de forma secuencial.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = BASE_DIR / "scripts"


def run_step(script_name: str) -> None:
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        raise FileNotFoundError(f"No existe el paso requerido: {script_path}")
    print(f"\n=== Ejecutando: {script_name} ===")
    subprocess.run([sys.executable, str(script_path)], check=True, cwd=str(BASE_DIR))


def main() -> None:
    steps = [
        "build_silver_dataset.py",
        "train_linear_heating_model.py",
        "build_silver_dataset.py",  # recalcula calefaccion_on_pred/target tras columna lineal
        "export_final_ia_dataset.py",
        "train_nn_derroche_model_keras.py",
    ]
    for step in steps:
        run_step(step)
    print("\nPipeline completado correctamente.")


if __name__ == "__main__":
    main()
