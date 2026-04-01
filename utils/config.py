from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

if ENV_FILE.exists():
    from dotenv import load_dotenv

    load_dotenv(ENV_FILE)

# PDF reference infra (documented requirement)
PDF_DB_HOST = "172.16.204.240"
PDF_DB_PORT = 5432
PDF_DB_NAME = "postgres"

# Active local infra (current project execution)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Weighted ventilation constants
WINDOW_WEIGHT_SMALL = 1
WINDOW_WEIGHT_LARGE = 2
DOOR_WEIGHT = 4
TOTAL_WEIGHT_DIVISOR = 20
DERROCHE_VENTILATION_THRESHOLD_PCT = 15.0

# CSV bronze (temperatura para normas de calefaccion / modelo lineal)
BRONZE_HISTORY_CSV = BASE_DIR / "data" / "bronze" / "History_2025-09-01_100-2026-03-02_1400.csv"