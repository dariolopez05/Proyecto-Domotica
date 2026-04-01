# Manual 1 Página (Profesor)

## Proyecto

**Eficiencia energética en aula**: detectar si habrá derroche en la siguiente hora.

---

## Problema que resolvemos

Se considera derroche cuando:

- la calefacción está encendida según normas sobre temperatura History (`calefaccion_on_normas_history = 1`)
- y la ventilación ponderada es **estrictamente mayor al 15 %** (`porcentaje_ventilacion_aula > 15`)

Objetivo de IA:

- predecir `target_derroche_next_hour` (derroche en la hora siguiente).

---

## Datos y arquitectura

- Fuente histórica en PostgreSQL/Timescale (`ltss`) + exportaciones locales.
- Arquitectura Medallion simplificada:
  - **Silver (master):** `data/silver/master_dataset.csv`
  - **Gold (dataset IA):** `data/gold/dataset_final_ia.csv`
- Fuente única de negocio SQL:
  - `queries/master_query.sql`

### Variables clave usadas

- Contexto temporal (cíclico): `hora_sin`/`hora_cos`, `dia_semana_sin`/`dia_semana_cos`, `mes_sin`/`mes_cos`
- Entorno: `temp_ext`, `viento`, `nubosidad`, `sol_elevacion`
- Aula: `temp_aula`, `humedad_aula`
- Ventilación: `porcentaje_ventilacion_aula`

---

## Reglas de negocio implementadas

- Pesos de aperturas:
  - ventana pequeña = 1
  - ventana grande = 2
  - puerta = 4
- Divisor total ponderado = 20
- Target futuro:
  - `target_derroche_next_hour = derroche.shift(-1)`

---

## Modelos implementados (según PDF)

## 1) Modelo ML lineal (T5-T6)

- Script: `scripts/train_linear_heating_model.py`
- Modelo: `LinearRegression`
- Finalidad: inferir `temp_calefaccion_lineal` para apoyar la detección del estado de calefacción.
- Artefactos:
  - `models/heating_linear_model.joblib`
  - `reports/heating_linear_model_metrics.txt`

## 2) Modelo IA (red neuronal) (Fase C)

- Script: `scripts/train_nn_derroche_model_keras.py`
- Modelo: TensorFlow/Keras (MLP tabular Dense → Dense → sigmoid)
- Target: `target_derroche_next_hour`
- Artefactos:
  - `models/nn_derroche_model_keras.keras`
  - `models/nn_derroche_preprocess_keras.joblib` (imputer, scaler, umbral)
  - `reports/nn_derroche_metrics_keras.txt`

---

## Ejecución rápida (demo)

Comando único:

```bash
python scripts/run_pipeline.py
```

Incluye:
1. Construcción Gold
2. Entrenamiento lineal
3. Rebuild Gold con columna lineal
4. Export dataset IA
5. Entrenamiento red neuronal (Keras)

Predicción manual por CLI:

```bash
python scripts/app_predict_derroche.py --fecha "2025-12-18 14:00:00" --temp-aula ... --temp-ext ... --humedad-aula ... --viento ... --nubosidad ... --sol-elevacion ... --porcentaje-ventilacion-aula ...
```

O con hora suelta: `--hora 14 --dia-semana 3 --mes 12` (día 0=Lunes…6=Domingo). El script calcula los seis senos/cosenos como en el CSV.

---

## Estado de entrega

- Fase A/B/C: implementadas en código y dataset.
- Fase D (dashboard Grafana): implementado en `grafana/` (Docker + import JSON).
- Presentación de cierre: pendiente.
- Memoria técnica: [`MEMORIA_TECNICA.md`](MEMORIA_TECNICA.md) (esta carpeta `docs/entrega/`).

Referencia de estado detallado del proyecto:

- [`../PROYECTO_ESTADO.md`](../PROYECTO_ESTADO.md)
