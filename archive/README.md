# Archive

Scripts movidos por refactor Medallion para evitar logica duplicada y mantener un unico flujo:

- `scripts/train_history_temperature_model.py` (RandomForest legacy)
- `scripts/add_temperature_history_prediction_to_master.py` (enriquecimiento legacy)
- `scripts/run_master_query.py` (duplicado de ejecucion SQL)
- `scripts/execute_master_query.py` (duplicado de ejecucion SQL)
- `scripts/build_final_ia_dataset.py` (reemplazado por flujo sobre `master_dataset.csv`)
- `queries/window-door_total.sql` (logica de ventilacion integrada en `queries/master_query.sql`)
- `queries/windows_agrupated.sql` (legacy)
- `queries/windows_agrupated_total.sql` (legacy)
- `queries/temperatures_aggrupated.sql` (legacy)
- `queries/media_temperature.sql` (legacy)
- `queries/media_temperature_humidity.sql` (legacy)
- `data/gold/master_query_result.csv` (legacy)
- `data/gold/master_query_result_with_temperature_history_pred.csv` (legacy)
- `data/gold/history_temperature_predictions.csv` (legacy)
- `reports/history_temperature_*` (legacy)

Ademas, se archivan (no forman parte del flujo principal):

- Notebooks de referencia:
  - `archive/notebooks/GerardLopez_ExamenPIA.ipynb`
- Scripts de analisis auxiliares:
  - `archive/scripts/analyze_sensors.py`
  - `archive/scripts/analyze_humidity_sensors.py`
  - `archive/scripts/analysis_master_query.py` / `.ps1`
- `docs_legacy/`: texto histórico; puede citar puertos o nombres de BD antiguos. Configuración vigente: `docs/`, `docs/entrega/`, `reports/` y `.env.example` en la raíz del proyecto.

Flujo activo actual:

1. `scripts/build_gold_dataset.py`
2. `scripts/train_linear_heating_model.py`
3. `scripts/export_final_ia_dataset.py`
4. `scripts/train_nn_derroche_model_keras.py`
5. `scripts/app_predict_derroche.py`

Archivos legacy adicionales (sustituidos por la versión Keras):

- `scripts/train_nn_derroche_model.py` -> `archive/scripts/train_nn_derroche_model_sklearn_legacy.py`
- `models/nn_derroche_model.joblib` -> `archive/models_legacy/nn_derroche_model_sklearn.joblib`
- `reports/nn_derroche_metrics.txt` -> `archive/reports/legacy/nn_derroche_metrics_sklearn.txt`
- `data/gold/nn_derroche_predictions.csv` -> `archive/data/gold_legacy/nn_derroche_predictions_sklearn.csv`
