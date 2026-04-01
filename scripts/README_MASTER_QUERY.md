# Scripts del Pipeline (Medallion)

Este directorio contiene el flujo operativo unificado del proyecto.

## Scripts activos (responsabilidad única)

- **`build_gold_dataset.py`**: construye `data/gold/master_dataset.csv` desde `queries/master_query.sql` (fuente única).
- **`train_linear_heating_model.py`**: entrena regresión lineal e inyecta `temp_calefaccion_lineal` en `master_dataset.csv`.
- **`export_final_ia_dataset.py`**: genera `data/gold/dataset_final_ia.csv` con las features finales y el target.
- **`train_nn_derroche_model_keras.py`**: entrena red neuronal binaria (TensorFlow/Keras) para `target_derroche_next_hour`.
- **`app_predict_derroche.py`**: app CLI para inferencia de derroche (`--hora 0-23` o `--hora-sin`/`--hora-cos`).
- **`run_pipeline.py`**: ejecuta todos los pasos en orden, de extremo a extremo.
- **`archive/scripts/run_master_query.ps1`**: utilidad legacy (no recomendada en el flujo principal).

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
python scripts/build_gold_dataset.py
python scripts/train_linear_heating_model.py
python scripts/build_gold_dataset.py
python scripts/export_final_ia_dataset.py
python scripts/train_nn_derroche_model_keras.py
```

## Output

Salidas principales:

```
data/gold/master_dataset.csv
data/gold/dataset_final_ia.csv
models/heating_linear_model.joblib
models/nn_derroche_model_keras.keras
models/nn_derroche_preprocess_keras.joblib
reports/heating_linear_model_metrics.txt
reports/nn_derroche_metrics_keras.txt
reports/nn_derroche_backtest_keras.txt
```

En `master_dataset.csv` quedan también derivadas:
- `% ventilación ponderada`
- `calefaccion_on_pred`
- `derroche`
- `target_derroche_next_hour`
- `hora_sin`, `hora_cos`

## Solución de problemas

### Error: "Archivo de consulta no encontrado"

Asegúrate de que existe `queries/master_query.sql`.

### Error: "Error de conexión PostgreSQL"

1. Verifica que PostgreSQL esté corriendo
2. Comprueba `.env`
3. Verifica host/puerto en `.env` (p. ej. `localhost` y `5432`)
4. `build_gold_dataset.py` usa fallback a CSV local si DB no está disponible

### Error: "Módulo no encontrado"

Reinstala dependencias:

```bash
pip install -r requirements.txt
```