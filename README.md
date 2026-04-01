# Domótica — Analítica e IA (derroche de calefacción)

Proyecto de eficiencia energética orientado a detectar derroche en la siguiente hora con una arquitectura Medallion simplificada.

## Estado actual (resumen rápido)

- Capa Gold unificada en `data/gold/master_dataset.csv`.
- Dataset final IA en `data/gold/dataset_final_ia.csv`.
- Modelo lineal para temperatura de calefacción y red neuronal para derroche entrenados.
- Scripts legacy movidos a `archive/scripts/`.
- Estado detallado y trazabilidad: `PROYECTO_ESTADO.md`.
- Guía de arquitectura y flujo: `docs/ARQUITECTURA_MEDALLION.md`.
- Manual breve para presentación: `docs/MANUAL_1_PAGINA_PROFESOR.md`.
- Auditoría técnica final: `docs/AUDITORIA_REPRODUCIBILIDAD.md`.

## Requisitos

- Python 3.10+ recomendado.
- Dependencias: `pip install -r requirements.txt` (incluye `pandas`, `scikit-learn`, `tensorflow-cpu`, `psycopg2-binary`, `python-dotenv`, etc.).

## Pipeline de punta a punta

```bash
python scripts/run_pipeline.py
```

Orden interno:

1. `build_gold_dataset.py` — SQL → Gold + normas History + derroche + target.
2. `train_linear_heating_model.py` — modelo lineal y columna `temp_calefaccion_lineal` en el master.
3. `build_gold_dataset.py` — reconstruye Gold con esa columna.
4. `export_final_ia_dataset.py` — `dataset_final_ia.csv` (solo calefacción on).
5. `train_nn_derroche_model_keras.py` — entrena y guarda modelo + preprocesado.

Si PostgreSQL no está disponible, `build_gold_dataset` puede usar un CSV Gold previo como respaldo (ver script).

## Conexión a base de datos

Copia `.env.example` a `.env` y ajusta host, puerto (p. ej. 5432), base de datos (p. ej. `postgres`), usuario y contraseña. La query principal usa la tabla **`ltss`**. Más detalle: `scripts/README_MASTER_QUERY.md`.

El entorno de la memoria PDF de asignatura puede describir otro host; el desarrollo ha sido con **PostgreSQL local** y la misma lógica de consultas.

## Predicción manual (CLI)

Ejemplo con fecha completa (recomendado; deriva hora, día de semana y mes como en el entrenamiento):

```bash
python scripts/app_predict_derroche.py --fecha "2025-12-18 14:00:00" --temp-aula 22 --temp-ext 15 --humedad-aula 50 --viento 10 --nubosidad 40 --sol-elevacion 20 --porcentaje-ventilacion-aula 10
```

Hace falta tener entrenados `models/nn_derroche_model_keras.keras` y `models/nn_derroche_preprocess_keras.joblib`.

## Estructura relevante del repositorio

```text
Proyecto-Domotica/
├── README.md
├── requirements.txt
├── .env.example
├── queries/
│   └── master_query.sql
├── scripts/              # pipeline, export, entrenamiento, app, informe
├── utils/                # config, db, preprocessing, normas calefacción
├── data/
│   ├── bronze/           # History CSV (temperatura normas / lineal)
│   └── gold/             # master_dataset, dataset_final_ia, predicciones
├── models/               # joblib + .keras
├── reports/              # métricas, informe HTML, auditoría reproducibilidad
├── docs/
│   ├── entrega/          # memoria técnica + manual 1 página (profesor)
│   ├── ARQUITECTURA_MEDALLION.md
│   └── PROYECTO_ESTADO.md
└── archive/              # scripts y artefactos legacy
```

## Indicaciones que han guiado el análisis (resumen)

- Sensores de temperatura en ventanas descartados para el foco del aula; correlación entre sensores internos llevó a quedarse con el **sensor 4** (centro).
- Ventanas **pares** = pequeñas (superiores), **impares** = grandes (inferiores); la ventana 11 dejó de ser fiable y se excluye de la lógica agregada.
- CSV de History de otra aula en la misma ala: se usa donde encaja con el uso pedagógico; el **master** horario viene de **vuestra** agregación SQL.

## To-do propio del repo (baja prioridad)

- Automatizar más el flujo de correlación de sensores si hiciera falta replicar análisis antiguos (`archive/scripts/`).
