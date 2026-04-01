# Comparativa: requisitos PDF (T10 BDA) vs implementación actual

Documento base: `T10 - Proyecto Domotica - BDA.pdf` (secciones 2–7).  
Estado del código y entregables: `docs/PROYECTO_ESTADO.md`.

Leyenda: **Cumple** | **Parcial / interpretación** | **No implementado / gap**

---

## 1. Infraestructura y sensores (sección 2 del PDF)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| TimescaleDB/PostgreSQL, `ltss` | **Cumple** (conexión vía `.env`; query en `queries/master_query.sql`). |
| **Shelly Pro EM-50** (consumo eléctrico) listado como sensor | **No implementado**: no hay columna ni entidad de consumo eléctrico en la query Gold ni en el modelo. |
| Aqara contactos, Aqara temp/humedad/presión, Met.no, Sun | **Parcial**: se usan entidades concretas en SQL (Mislata meteo, sensor 4 aula, contactos en lista fija); no se reflejan todos los nombres del PDF si difieren del despliegue real. |

---

## 2. Objetivos generales (sección 3)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| Recopilar y preparar datos por horas | **Cumple** (`build_gold_dataset.py`, `master_query.sql`). |
| Analizar correlaciones (optimizar sensores) | **Cumple** (scripts en `archive/scripts/`, informes humedad/temperatura). |
| Detectar/predicir si la calefacción está encendida | **Cumple** (`calefaccion_on_normas_history`, `calefaccion_on_pred`). |
| Modelo ML + modelo IA | **Cumple** (lineal + Keras). |
| **Dashboard** tiempo real e histórico | **No implementado** (Grafana pendiente; ver `PROYECTO_ESTADO.md`). |

---

## 3. Entregables (sección 4)

| Entregable PDF | Estado en el proyecto |
|----------------|------------------------|
| Documento técnico (PDF) con decisiones, justificación, resultados | **Parcial**: contenido en `docs/entrega/MEMORIA_TECNICA.md`; exportación a PDF depende de la entrega del grupo. |
| Scripts/SQL extracción, limpieza, agregación | **Cumple** (`scripts/`, `queries/`). |
| **Notebooks** tipo `01_eda.ipynb` … `05_evaluation.ipynb` (estructura ejemplo) | **No replicado** tal cual: el flujo está en scripts Python; no hay carpeta `notebooks/` obligatoria con esa numeración. |
| Modelo ML + métricas | **Cumple** (`models/heating_linear_model.joblib`, `reports/heating_linear_model_metrics.txt`). |
| Red neuronal + métricas | **Cumple** (`models/nn_derroche_model_keras.keras`, `reports/nn_derroche_metrics_keras.txt`). |
| **Dashboard funcional** HA/TimescaleDB + visualizaciones | **No implementado** (sin carpeta `dashboard/` ni Grafana en repo). |
| Presentación 5–8 diapos | **Pendiente** (material fuera del repo o por añadir). |
| Estructura repo ejemplo (`bronze/silver/gold`, `sql/01_...`) | **Parcial**: hay `data/bronze`, `data/gold`; **no hay capa Silver** explícita; SQL principal en `queries/` no en `sql/` con ese numerado. |

---

## 4. Fase A — T1 Target (sección 6)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| Target binario derroche; **anticipación** (siguiente hora) | **Cumple** (`target_derroche_next_hour`). |
| Umbral derroche “10 %, 20 % …” (ejemplos) | **Parcial**: criterio operativo fijado en **> 15 %** ventilación ponderada + calefacción on (`DERROCHE_VENTILATION_THRESHOLD_PCT`); documentado en memoria/README. |
| Ventana inferior = 2× superior; puerta = 2 ventanas inferiores | **Cumple** (pesos 1 / 2 / 4 y divisor 20 en SQL + `config.py`). |

---

## 5. Fase B — Datos y CSV horario (T1–T3 PDF)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| Correlaciones temperatura / humedad | **Cumple** (análisis archivados + informes). |
| CSV horario con **hora, día semana, mes** | **Cumple**: en **`master_dataset.csv`** hay `datetime`, `hora`, `dia_semana`, `mes`. En **`dataset_final_ia.csv`** entran como **seno/coseno** (`hora_*`, `dia_semana_*`, `mes_*`) para el modelo. |
| **Temperaturas, humedad, presión de cada sensor del aula** | **Parcial**: tras correlación se consolidó en **un sensor de temperatura/humedad de aula** (sensor 4 en query), no una columna por cada sensor físico del PDF. |
| Puertas/ventanas: **minutos abiertos** en la hora | **Parcial**: hay **ventilación ponderada** y `porcentaje_ventilacion_aula` (y minutos ponderados en lógica SQL), no el mismo enunciado “minutos crudos” por entidad; el umbral de derroche es sobre **%** (>15 %), no sobre “> X minutos” literal del PDF. |
| Exteriores: temp exterior, nubosidad, sol, etc. | **Cumple** en master (meteo + sol); en dataset IA faltan **presión** y **dirección de viento** respecto a lo que el master sí tiene. |

---

## 6. Fase B — T4–T9 (modelo lineal, columnas, derroche)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| T4–T5: ML lineal + columna temp calefacción inferida | **Cumple** (`temp_calefaccion_lineal`). |
| T6: columna calefacción encendida | **Cumple** (`calefaccion_on_pred` + normas History). |
| T7: minutos abiertos + derroche si calefacción + abiertos **> X minutos** | **Parcial**: lógica equivalente vía **porcentaje de ventilación** y umbral **15 %**; no es “minutos” directos en la condición final. |
| T8: derroche en hora siguiente | **Cumple** (`target_derroche_next_hour`). |
| **T9 CSV definitivo para IA** (lista explícita PDF) | Hora/día/mes como features cíclicas; ver tabla T9 ↓ |

### T9 — Columnas que el PDF pide en el CSV final vs `dataset_final_ia.csv`

| Columna / concepto (PDF) | En `dataset_final_ia.csv` |
|----------------------------|---------------------------|
| Hora del día | **Cumple (codificación cíclica)**: `hora_sin`, `hora_cos` (equivalente legible: hora 0–23). |
| Día de la semana | **Cumple (codificación cíclica)**: `dia_semana_sin`, `dia_semana_cos` (0=Lunes … 6=Domingo en origen). |
| Mes del año | **Cumple (codificación cíclica)**: `mes_sin`, `mes_cos` (mes 1–12). |
| Temperaturas/humedad/presión **por sensor** | **Parcial**: solo **`temp_aula`**, **`humedad_aula`** (representación agregada), **sin presión** en el CSV IA. |
| Sensores externos (temp ext, nubosidad, sol, etc.) | **Parcial**: `temp_ext`, `nubosidad`, `sol_elevacion`, `viento`; **no** `presion`, **no** `direccion_viento`, **no** `forecast` en el CSV IA. |
| **Si está encendida la calefacción** | **No** como feature: se usa para **filtrar** filas al exportar, pero **no** se incluye `calefaccion_on_*` en las columnas del entrenamiento (evitar fuga/redundancia según diseño actual). |
| Target: derroche hora siguiente | **Cumple** (`target_derroche_next_hour`). |

El PDF sugiere además quitar columnas que generen ruido; el proyecto **omite** explícitamente minutos abiertos crudos, temp calefacción inferida, etc., del CSV IA — **alineado en espíritu**, con lista de columnas distinta a la del enunciado literal.

---

## 7. Fase C — Red neuronal y app (T10–T11)

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| Red neuronal binaria + métricas + justificación | **Cumple** (Keras, métricas en `reports/`). |
| App para introducir datos y ver derroche siguiente hora | **Parcial**: **CLI** `scripts/app_predict_derroche.py` (con `--hora`); el PDF puede interpretarse como app con **interfaz gráfica** — **no** hay app web en el repo. |

---

## 8. Fase D — Grafana

| Requisito PDF | Estado en el proyecto |
|----------------|------------------------|
| Mínimo 2 visualizaciones (serie temporal temperatura; gauge temperatura media) | **No implementado**. |
| Variable para **seleccionar sensor** de temperatura | **No implementado**. |

---

## 9. Resumen de gaps respecto al PDF (accionables)

1. **Dashboard Grafana** (Fase D completa).  
2. **Presentación** 5–8 diapos.  
3. **Documento técnico en PDF** si el centro exige formato PDF explícito (contenido ya en memoria Markdown).  
4. **Consumo eléctrico (Shelly)** no integrado en datos ni modelos.  
5. **CSV final IA**: **hora, día de semana y mes** están cubiertos como **features cíclicas** (`*_sin`/`*_cos`). Pueden faltar aún **presión** y otros campos del master si se quiere paridad con el enunciado literal. **Calefacción on** sigue siendo filtro de export, no feature.  
6. **App**: solo CLI; una app web no está desarrollada.  
7. **Estructura ejemplo** (silver, notebooks numerados, `sql/01_...`): no replicada al pie de la letra.

---

*Esta comparativa no sustituye al tribunal ni al criterio del profesorado; sirve para priorizar trabajo y argumentar decisiones en la defensa.*
