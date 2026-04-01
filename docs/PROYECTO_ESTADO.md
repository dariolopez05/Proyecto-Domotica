# PROYECTO DOMOTICA - ESTADO ACTUAL (ALINEADO CON "T10 - PROYECTO DOMOTICA - BDA")

## 1) Infraestructura (segun PDF vs estado real)

- **PDF indica:** TimescaleDB/PostgreSQL en `172.16.204.240:5432`, BD `postgres`.
- **Estado actual del proyecto:** PostgreSQL local (p. ej. `localhost:5432`), BD `postgres`, usuario `postgres` (credenciales en `.env`).
- **Decision actual:** trabajar en local para desarrollo/ejecucion de scripts.
- **Impacto:** las queries y scripts son validos, pero para entrega hay que documentar claramente esta diferencia respecto al entorno del PDF.

## 2) Estructura de datos y base de datos actual

### 2.1 Origen de datos
- **Tabla operativa:** `ltss`.
- **Campos usados:** `time`, `entity_id`, `state`, `attributes`.
- **Fuentes integradas en consultas:**
  - Sensores de aula (temperatura/humedad).
  - Contactos puerta/ventanas.
  - Sensores externos meteo.
  - Variables solares y forecast.

### 2.2 Capa Silver (tabla maestra horaria) y Gold (consumo ML)
- **Fuente única SQL:** `queries/master_query.sql`.
- **Salida capa Silver:** `data/silver/master_dataset.csv` (tabla consolidada + reglas de negocio).
- **Salida capa Gold:** `data/gold/dataset_final_ia.csv`, `data/gold/nn_derroche_predictions_keras.csv`.
- **Columnas clave (master):** `datetime`, `dia_semana`, `mes`, `hora`, meteo exterior, solares, `temperatura_aula`, `humedad_aula`, `forecast`, `porcentaje_ventilacion_aula`.

### 2.3 Arquitectura actual (refactor Medallion)
- **`utils/config.py`**: constantes de infraestructura, negocio (pesos/divisor) y rutas Silver/Gold.
- **`utils/db_manager.py`**: conexión y ejecución de queries PostgreSQL.
- **`utils/preprocessing.py`**: ventilación, escalado IA, derroche y target siguiente hora.
- **`scripts/build_silver_dataset.py`**: constructor Silver (master horario).
- **`scripts/run_pipeline.py`**: orquestación end-to-end.
- **`archive/scripts/`**: scripts legacy/duplicados retirados del flujo principal.

## 3) Logica de pesos de ventanas/puerta (requisito explicito del PDF)

- Regla pedida en PDF: ventana inferior = 2x superior; puerta equivalente reforzada.
- **Implementado en SQL/script:**
  - Ventanas impares: **peso 2**.
  - Ventanas pares: **peso 1**.
  - Puerta 1: **peso 4** (equivale a dos ventanas inferiores).
- **Fuente activa donde se aplica:** `queries/master_query.sql`.
- **Consultas legacy (referencia histórica):**
  - `archive/queries/windows_agrupated_total.sql`
  - `archive/queries/window-door_total.sql`
- **Metricas derivadas:**
  - `total_ventilacion_ponderada_min`
  - `porcentaje_ventilacion_aula`

## 4) Estado por fases/tareas del PDF (T1-T11)

## Fase A - Definicion del problema

- **T1 Target:** **HECHO (documentado)**
  - Derroche: calefaccion on (normas History) + ventilacion ponderada **> 15 %** (`DERROCHE_VENTILATION_THRESHOLD_PCT`).
  - Criterio unico descrito en `docs/entrega/MEMORIA_TECNICA.md` y `README.md`.

## Fase B - Recopilacion y preparacion de datos

- **T2 Correlaciones temperatura:** **HECHO**
  - Evidencia: `archive/scripts/analyze_sensors.py` y decision de quedarse con sensor 4.
- **T3 Correlaciones humedad:** **HECHO**
  - Evidencia: `archive/scripts/analyze_humidity_sensors.py` + artefactos en `reports/humidity_analysis/`.
- **T4 Recopilar datos por hora:** **HECHO**
  - Evidencia: `queries/master_query.sql` + `scripts/build_silver_dataset.py`.
- **T5 Calculo temperatura calefaccion + modelo ML lineal:** **HECHO**
  - Evidencia: `scripts/train_linear_heating_model.py` (LinearRegression) + `models/heating_linear_model.joblib`.
- **T6 Nueva columna temperatura calefaccion inferida:** **HECHO**
  - Evidencia: columna `temp_calefaccion_lineal` en `data/silver/master_dataset.csv`.
- **T7 Nueva columna calefaccion encendida:** **HECHO**
  - Evidencia: `calefaccion_on_pred` generada por `scripts/build_silver_dataset.py` (schedule con histéresis).
- **T8 Derroche (minutos abiertos + flag derroche):** **HECHO**
  - Regla aplicada: `derroche = (calefaccion_on_pred == 1) AND (porcentaje_ventilacion_aula > 15)`.
- **T9 Derroche en hora siguiente:** **HECHO**
  - Evidencia: columna `target_derroche_next_hour = derroche.shift(-1)`.
- **T10 CSV final solo con columnas necesarias para IA:** **HECHO**
  - Evidencia: `scripts/export_final_ia_dataset.py` -> `data/gold/dataset_final_ia.csv`.

## Fase C - Modelo de IA

- **T10 (PDF) Red neuronal binaria derroche si/no:** **HECHO**
  - Evidencia: `scripts/train_nn_derroche_model_keras.py`, `models/nn_derroche_model_keras.keras`, `reports/nn_derroche_metrics_keras.txt`.
- **T11 App de prediccion de derroche:** **HECHO (CLI + app web)**
  - Evidencia: `scripts/app_predict_derroche.py` (CLI); `web_app/app.py` + plantillas (Flask, predicción vía API / interfaz).

- **Dataset final IA + predicciones (pipeline cerrado para entrega):** **CERRADO**
  - `data/gold/dataset_final_ia.csv`, export con filtro calefaccion on + huecos imputados en entrenamiento; `scripts/generate_data_report.py` para informe HTML legible.

## Fase D - Dashboard

- **Dashboard en Grafana con min. 2 visualizaciones + selector sensor:** **HECHO**
  - Artefactos en `grafana/`: `docker-compose.yml`, provisioning PostgreSQL (`provisioning/datasources/`), dashboard JSON `dashboards/domotica-temperatura.json` (serie temporal + gauge de media + variable sensor). Instrucciones: `grafana/README.md`.

## 5) Modelos y artefactos ya generados

- **Modelos entrenados actuales:**
  - `LinearRegression` para temperatura calefaccion (`scripts/train_linear_heating_model.py`).
  - `TensorFlow/Keras` (red neuronal) para `target_derroche_next_hour` (`scripts/train_nn_derroche_model_keras.py`).
- **Artefactos:**
  - `models/heating_linear_model.joblib`
  - `models/nn_derroche_model_keras.keras`
  - `models/nn_derroche_preprocess_keras.joblib` (incluye umbral)
  - `data/silver/heating_linear_predictions.csv`
  - `data/silver/master_dataset.csv`
  - `data/gold/dataset_final_ia.csv`
  - `data/gold/nn_derroche_predictions_keras.csv`
  - `reports/heating_linear_model_metrics.txt`
  - `reports/nn_derroche_metrics_keras.txt`
  - `reports/nn_derroche_backtest_keras.txt`
  - `reports/humidity_analysis/*`

## 6) Entregables del PDF: estado rapido

- Documento tecnico (memoria Markdown + export PDF opcional): **HECHO** (`docs/entrega/MEMORIA_TECNICA.md`); PDF de entrega si el centro lo pide: generar desde el .md o adjuntar impresion.
- Scripts SQL/Python de extraccion y agregacion: **HECHO**.
- Modelo ML lineal entrenado + metricas: **HECHO**.
- Red neuronal entrenada + metricas: **HECHO**.
- Dashboard funcional (Grafana/HA/Timescale): **HECHO** (Grafana en `grafana/`).
- Presentacion 5-8 diapositivas: **PENDIENTE**.

## 7) Proximos pasos (orden recomendado para cumplir PDF)

1. Presentacion 5-8 diapositivas con evidencia (metricas, consultas, graficas, Grafana, app web); memoria tecnica en `docs/entrega/MEMORIA_TECNICA.md`.
2. Exportar memoria a **PDF** si el centro lo exige.

## 8) Flujo operativo actual (comando único)

```bash
python scripts/run_pipeline.py
```

Ejecuta secuencialmente:
1. `build_silver_dataset.py`
2. `train_linear_heating_model.py`
3. `build_silver_dataset.py` (reconstruye target con temperatura lineal)
4. `export_final_ia_dataset.py`
5. `train_nn_derroche_model_keras.py`

## 9) Documentación viva

- Arquitectura y responsabilidades por componente:
  - `docs/ARQUITECTURA_MEDALLION.md`
- Manual ejecutivo de 1 página (orientado a defensa/entrega):
  - `docs/entrega/MANUAL_1_PAGINA_PROFESOR.md`
- Auditoría final de reproducibilidad:
  - `reports/AUDITORIA_REPRODUCIBILIDAD.md`
- Estado y trazabilidad de tareas PDF:
  - `docs/PROYECTO_ESTADO.md` (este archivo)
- Memoria tecnica (decisiones y justificaciones):
  - `docs/entrega/MEMORIA_TECNICA.md`
- Uso operativo de scripts:
  - `scripts/README_MASTER_QUERY.md`
- Comparativa requisitos PDF vs implementacion:
  - `docs/COMPARATIVA_REQUISITOS_PDF.md`
