# Manual 1 Página (Profesor)

## Proyecto

**Eficiencia energética en aula**: detectar si habrá derroche en la siguiente hora.

---

## Problema que resolvemos

Se considera derroche cuando:

- la calefacción está encendida (`calefaccion_on_pred = 1`)
- y la ventilación ponderada supera el 15% (`porcentaje_ventilacion_aula > 15`)

Objetivo de IA:

- predecir `target_derroche_next_hour` (derroche en la hora siguiente).

---

## Datos y arquitectura

- Fuente histórica en PostgreSQL/Timescale (`ltss`) + exportaciones locales.
- Arquitectura Medallion simplificada:
  - **Gold unificado:** `data/gold/master_dataset.csv`
  - **Dataset IA final:** `data/gold/dataset_final_ia.csv`
- Fuente única de negocio SQL:
  - `queries/master_query.sql`

### Variables clave usadas

- Contexto temporal: `hora_sin`, `hora_cos`
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

- Script: `scripts/train_nn_derroche_model.py`
- Modelo: `MLPClassifier` (clasificación binaria)
- Target: `target_derroche_next_hour`
- Artefactos:
  - `models/nn_derroche_model.joblib`
  - `reports/nn_derroche_metrics.txt`

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
5. Entrenamiento red neuronal

Predicción manual por CLI:

```bash
python scripts/app_predict_derroche.py --hora-sin ... --hora-cos ... --temp-aula ... --temp-ext ... --humedad-aula ... --viento ... --nubosidad ... --sol-elevacion ... --porcentaje-ventilacion-aula ...
```

---

## Estado de entrega

- Fase A/B/C: implementadas en código y dataset.
- Fase D (dashboard Grafana): pendiente.
- Presentación y memoria técnica final: pendiente de cierre documental.

Referencia de estado detallado:

- `PROYECTO_ESTADO.md`
