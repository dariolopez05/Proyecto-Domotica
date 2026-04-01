# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

An energy efficiency analytics pipeline for a school building that predicts energy waste (heating on while windows/doors are open) in the next hour. Data comes from a Home Assistant PostgreSQL database with temperature, ventilation, and weather sensors.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env  # then fill in DB credentials
```

Database connection is optional — scripts fall back to local CSV files if PostgreSQL is unavailable.

## Running the Pipeline

```bash
# Full pipeline (runs all 5 steps sequentially, ~1-2 minutes)
python scripts/run_pipeline.py

# Individual steps
python scripts/build_silver_dataset.py
python scripts/train_linear_heating_model.py
python scripts/export_final_ia_dataset.py
python scripts/train_nn_derroche_model_keras.py

# CLI prediction (all 9 features required)
python scripts/app_predict_derroche.py \
  --hora-sin -0.259 --hora-cos -0.966 \
  --temp-aula 21.8 --temp-ext 11.9 \
  --humedad-aula 49.65 --viento 40.0 \
  --nubosidad 98.4 --sol-elevacion 27.1 \
  --porcentaje-ventilacion-aula 0.06
```

## Architecture

### Data Flow (Medallion Pattern)

```
PostgreSQL (ltss) or local CSV
         │
    master_query.sql  ← single source of truth for all sensor data
         │
    build_silver_dataset.py
         ├─ adds heating schedule state (schedule + hysteresis)
         ├─ adds derroche target (heat_on AND vent>15%)
         ├─ adds hour_sin/hour_cos cyclical features
         │
    data/silver/master_dataset.csv  (≈9,262 rows)
         │
    ┌────┴──────────────────────┐
    │                           │
train_linear_heating_model.py   export_final_ia_dataset.py
    │ (uses History_*.csv)           │
    ▼                           data/gold/dataset_final_ia.csv (≈5,170 rows)
heating_linear_model.joblib          │
    │ (inject temp predictions)       │
    └──────────────────────────►train_nn_derroche_model_keras.py
                                     │
                          nn_derroche_model_keras.keras
                          nn_derroche_preprocess_keras.joblib
```

### Key Business Logic

**Waste (`derroche`) definition:**
- Heating is ON (`calefaccion_on_pred == 1`) AND ventilation > 15%
- Target is shifted 1 hour forward: predict waste in the *next* hour

**Ventilation calculation** (in `utils/config.py` and `master_query.sql`):
- Weights: door=4, large windows=2, small windows=1, divisor=20
- Window 11 excluded (erratic readings after Oct 2025)
- Only sensor #4 used for classroom temp (others are 99.9% correlated)

**Heating state machine** — schedule-based with hysteresis (Mon–Fri only):
- T_off=22.0°C, T_on=21.9°C during school slots
- OFF outside school hours

**Neural network:**
- Architecture: Dense(128) → Dense(64) → Dense(1, sigmoid)
- Threshold: 0.30 (optimized for F1, not default 0.50)
- Classes are imbalanced (~90% no-waste / 10% waste)

### Module Responsibilities

| Path | Role |
|------|------|
| `utils/config.py` | Business constants: DB params, ventilation weights, thresholds |
| `utils/db_manager.py` | PostgreSQL connection with CSV fallback |
| `utils/preprocessing.py` | Ventilation normalization, target creation, cyclical encoding |
| `queries/master_query.sql` | Hourly aggregation SQL (135 lines, 2+ CTEs) |
| `scripts/run_pipeline.py` | Orchestrator — runs all steps in order |
| `data/silver/` | Master hourly table + linear model sidecar CSVs |
| `data/gold/` | ML-ready dataset + NN predictions |
| `models/` | Persisted model files (joblib + .keras) |
| `reports/` | Evaluation metrics and confusion matrices |
| `archive/` | Superseded scripts and queries — do not use |

## Model Performance (Test Set, 1,034 rows)

- **Linear heating model:** MAE 1.05°C, RMSE 1.35°C, R² 0.13
- **NN waste classifier:** Accuracy 85.78%, F1 0.2829, ROC-AUC 0.7539, threshold=0.30
