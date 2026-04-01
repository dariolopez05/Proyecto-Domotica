# Scripts del Pipeline (Medallion)

Este directorio contiene el flujo operativo unificado del proyecto.

## Scripts activos (responsabilidad única)

- **`build_silver_dataset.py`**: construye `data/silver/master_dataset.csv` desde `queries/master_query.sql` (fuente única).
- **`train_linear_heating_model.py`**: entrena regresión lineal e inyecta `temp_calefaccion_lineal` en el master (Silver); escribe `data/silver/heating_linear_predictions.csv`.
- **`export_final_ia_dataset.py`**: genera `data/gold/dataset_final_ia.csv` con las features finales y el target (lee desde Silver).
- **`train_nn_derroche_model_keras.py`**: entrena red neuronal binaria (TensorFlow/Keras) para `target_derroche_next_hour`; escribe predicciones en Gold.
- **`app_predict_derroche.py`**: app CLI para inferencia de derroche (`--hora 0-23` o `--hora-sin`/`--hora-cos`).
- **`run_pipeline.py`**: ejecuta todos los pasos en orden, de extremo a extremo.
- **`archive/scripts/run_master_query.ps1`**: utilidad legacy (no recomendada en el flujo principal).

Rutas canónicas: `utils/config.py` (`MASTER_DATASET_CSV`, `DATASET_FINAL_IA_CSV`, etc.).

## Requisitos

### 1. Instalar dependencias Python

```bash
pip install -r requirements.txt
```

O instalar directamente (mínimo):

```bash
pip install pandas psycopg2-binary python-dotenv scikit-learn joblib tensorflow-cpu
```

### 2. Configurar conexión a PostgreSQL

Las credenciales se configuran en el archivo `.env` en la raíz del proyecto.

**Variables típicas** (copia `.env.example` a `.env` y rellena):

- Host: `localhost`
- Puerto: `5432` (o el que uses)
- Base de datos: `postgres` (o la que contenga `ltss`)
- Usuario / contraseña: según tu instalación

```
DB_HOST=localhost
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=tu_contraseña
```

> ⚠️ **IMPORTANTE**: El archivo `.env` contiene credenciales y NO debe ser commiteado a git. Está en `.gitignore`.

## Uso recomendado

### Pipeline completo

```bash
python scripts/run_pipeline.py
```

### Ejecución por pasos

```bash
python scripts/build_silver_dataset.py
python scripts/train_linear_heating_model.py
python scripts/build_silver_dataset.py
python scripts/export_final_ia_dataset.py
python scripts/train_nn_derroche_model_keras.py
```

## Output

Salidas principales:

```
data/silver/master_dataset.csv
data/silver/heating_linear_predictions.csv
data/gold/dataset_final_ia.csv
data/gold/nn_derroche_predictions_keras.csv
models/heating_linear_model.joblib
models/nn_derroche_model_keras.keras
models/nn_derroche_preprocess_keras.joblib
reports/heating_linear_model_metrics.txt
reports/nn_derroche_metrics_keras.txt
reports/nn_derroche_backtest_keras.txt
```

En `master_dataset.csv` (Silver) quedan también derivadas:
- `% ventilación ponderada`
- `calefaccion_on_pred`
- `derroche`
- `target_derroche_next_hour`
- `hora_sin`, `hora_cos`, `dia_semana_sin`, `dia_semana_cos`, `mes_sin`, `mes_cos`

## Solución de problemas

### Error: "Archivo de consulta no encontrado"

Asegúrate de que existe `queries/master_query.sql`.

### Error: "Error de conexión PostgreSQL"

1. Verifica que PostgreSQL esté corriendo
2. Comprueba `.env`
3. Verifica host/puerto en `.env` (p. ej. `localhost` y `5432`)
4. `build_silver_dataset.py` usa fallback a CSV local si DB no está disponible

### Error: "Módulo no encontrado"

Reinstala dependencias:

```bash
pip install -r requirements.txt
```
