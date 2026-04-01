# Arquitectura Medallion (Guía Clara)

## 1. Objetivo

Este proyecto busca predecir si habrá **derroche energético en la siguiente hora**.

Derroche se define como:

- `calefaccion_on_normas_history == 1` (si existe; si no, `calefaccion_on_pred == 1`)
- y `porcentaje_ventilacion_aula > 15` (umbral fijado en `utils/config.py`)

Después se crea el target futuro:

- `target_derroche_next_hour = derroche.shift(-1)`

---

## 2. Capas de datos

## Bronze

- Datos de origen y exportaciones históricas.
- Ruta típica: `data/bronze/`.

## Gold (fuente operativa principal)

- Archivo maestro: `data/gold/master_dataset.csv`.
- Es la tabla consolidada por hora para análisis y modelado.

## Dataset final IA

- Archivo para entrenar la red neuronal:
  - `data/gold/dataset_final_ia.csv`
- Contiene solo features finales + target.

---

## 3. Fuente única de verdad

- SQL principal: `queries/master_query.sql`.
- Incluye:
  - variables meteo (Mislata),
  - variables solares,
  - variables del aula,
  - ventilación ponderada (ventanas + puerta).

---

## 4. Utilidades centralizadas (`utils/`)

## `utils/config.py`

- Constantes de conexión DB.
- Pesos de ventilación:
  - ventana pequeña: `1`
  - ventana grande: `2`
  - puerta: `4`
- Divisor total: `20`.

## `utils/db_manager.py` / `utils/config.py`

- `config.py` carga `.env` al importarse (si existe) y define `DB_HOST`, `DB_PORT`, `DB_NAME`, etc.
- `db_manager.py` abre conexión PostgreSQL y devuelve DataFrame desde SQL.

## `utils/preprocessing.py`

- Normaliza `% ventilación`.
- Añade `derroche` y `target_derroche_next_hour`.
- Genera codificación cíclica: `hora_sin`/`hora_cos`, `dia_semana_sin`/`dia_semana_cos`, `mes_sin`/`mes_cos`.
- Escalado de features para IA (`StandardScaler`).

---

## 5. Scripts activos (responsabilidad única)

## `scripts/build_gold_dataset.py`

- Construye `master_dataset.csv`.
- Añade calendario (`dia_semana`, `mes`, `hora`).
- Añade lógica de calefacción (`calefaccion_on_pred`).
- Añade target de derroche.
- Si PostgreSQL no está disponible, usa fallback local.

## `scripts/train_linear_heating_model.py`

- Entrena modelo lineal de temperatura de calefacción.
- Guarda:
  - `models/heating_linear_model.joblib`
  - `reports/heating_linear_model_metrics.txt`
  - `data/gold/heating_linear_predictions.csv`
- Inyecta `temp_calefaccion_lineal` en `master_dataset.csv`.

## `scripts/export_final_ia_dataset.py`

- Extrae desde `master_dataset.csv` las columnas finales de IA.
- Genera `data/gold/dataset_final_ia.csv`.

## `scripts/train_nn_derroche_model_keras.py`

- Entrena red neuronal (TensorFlow/Keras, MLP tabular) binaria para `target_derroche_next_hour`.
- Guarda:
  - `models/nn_derroche_model_keras.keras`
  - `models/nn_derroche_preprocess_keras.joblib`
  - `reports/nn_derroche_metrics_keras.txt`
  - `data/gold/nn_derroche_predictions_keras.csv`

## `scripts/app_predict_derroche.py`

- App CLI para inferencia manual.
- Devuelve predicción y probabilidad de derroche de la siguiente hora.

## `scripts/run_pipeline.py`

- Orquestador end-to-end del flujo completo.

---

## 6. Orden recomendado de ejecución

```bash
python scripts/run_pipeline.py
```

Internamente ejecuta:

1. `build_gold_dataset.py`
2. `train_linear_heating_model.py`
3. `build_gold_dataset.py` (reconstrucción con columna lineal)
4. `export_final_ia_dataset.py`
5. `train_nn_derroche_model_keras.py`

---

## 7. Scripts legacy

- Todo lo antiguo o duplicado se mueve a `archive/scripts/`.
- No forman parte del flujo principal.

---

## 8. Troubleshooting rápido

## Error DB

- Revisa `.env` (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).
- Si la DB local está caída, `build_gold_dataset.py` usa fallback CSV.

## Dependencias

```bash
pip install -r requirements.txt
```
