from __future__ import annotations

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE = BASE_DIR / ".env"

# PDF reference infra (documented requirement)
PDF_DB_HOST = "172.16.204.240"
PDF_DB_PORT = 5432
PDF_DB_NAME = "postgres"

# Active local infra (current project execution)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5433"))
DB_NAME = os.getenv("DB_NAME", "domotica")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Weighted ventilation constants
WINDOW_WEIGHT_SMALL = 1
WINDOW_WEIGHT_LARGE = 2
DOOR_WEIGHT = 4
TOTAL_WEIGHT_DIVISOR = 20
DERROCHE_VENTILATION_THRESHOLD_PCT = 15.0

