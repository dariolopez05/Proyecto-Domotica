# Auditoría de Reproducibilidad (Final)

Fecha: 2026-03-26

## Alcance

Se auditó la reproducibilidad técnica del flujo activo:

- `scripts/run_pipeline.py`
- `scripts/build_gold_dataset.py`
- `scripts/train_linear_heating_model.py`
- `scripts/export_final_ia_dataset.py`
- `scripts/train_nn_derroche_model_keras.py`

---

## Resultado ejecutivo

- Estado general: **APTO CON OBSERVACIÓN**
- Pipeline ejecuta de inicio a fin: **Sí**
- Integridad del target final IA: **Sí**
- Riesgo de data leakage en escalado NN: **Corregido**
- Centralización de pesos de ventilación: **Cumplida en flujo activo**

Observación principal:

- PostgreSQL local no estaba disponible durante la auditoría, por lo que el pipeline usó fallback local de CSV.

---

## Checklist de control

## 1) Entorno y dependencias

- Python: **3.10.11**
- Imports críticos (`pandas`, `numpy`, `sklearn`, `joblib`, `psycopg2`, `dotenv`, `tensorflow`/`keras`): **OK**
- `requirements.txt` actualizado con dependencias del flujo: **OK**

## 2) Ejecución end-to-end

- Comando auditado:
  - `python scripts/run_pipeline.py`
- Resultado:
  - pipeline completado correctamente
  - artefactos regenerados

## 3) Integridad de datasets

- `data/gold/master_dataset.csv`: **9261 filas**
- `data/gold/dataset_final_ia.csv`: **5169 filas**
- `target_derroche_next_hour` nulos en dataset final IA: **0**
- Columnas finales IA: **exactas** (10 columnas esperadas)

## 4) Data leakage (NN)

- Estado: **RESUELTO**
- Validación:
  - En Keras, el preprocesado (`SimpleImputer` + `StandardScaler`) se ajusta solo con train y se guarda en `models/nn_derroche_preprocess_keras.joblib`.
  - El umbral de decisión se selecciona en validación temporal y se guarda en el mismo artefacto.

## 5) Pesos de ventilación

- Estado: **RESUELTO EN FLUJO ACTIVO**
- Validación:
  - Pesos y divisor definidos en `utils/config.py`.
  - `queries/master_query.sql` usa placeholders.
  - `scripts/build_gold_dataset.py` inyecta constantes en runtime.

Nota:

- Existen hardcodes históricos en `archive/` (solo referencia, no ejecución activa).

---

## Hallazgos y acciones

## Hallazgo A (alto impacto operativo)

- **DB local inaccesible** durante la auditoría (servidor no disponible / credenciales no cargadas; el pipeline usó fallback CSV).
- Mitigación actual:
  - fallback automático a CSV local.
- Riesgo residual:
  - el pipeline puede no reflejar datos nuevos si DB no está levantada.

Acción recomendada:

- Levantar PostgreSQL antes de ejecución de entrega y relanzar pipeline para evidencias actualizadas.

## Hallazgo B (bajo impacto)

- Persisten utilidades legacy (PowerShell/archivos históricos).
- Estado:
  - aislados en `archive/` o marcados como legacy.

Acción recomendada:

- Mantenerlos fuera del flujo principal y no citarlos en la defensa técnica como ruta activa.

---

## Criterio de aprobación para entrega

Se considera reproducible en entorno de evaluación cuando:

1. `pip install -r requirements.txt` termina sin error.
2. PostgreSQL está activo con credenciales válidas en `.env`.
3. `python scripts/run_pipeline.py` termina en éxito.
4. Se generan/actualizan:
   - `data/gold/master_dataset.csv`
   - `data/gold/dataset_final_ia.csv`
   - `models/heating_linear_model.joblib`
   - `models/nn_derroche_model_keras.keras`
   - `models/nn_derroche_preprocess_keras.joblib`
   - `reports/heating_linear_model_metrics.txt`
   - `reports/nn_derroche_metrics_keras.txt`
   - `reports/nn_derroche_backtest_keras.txt`
