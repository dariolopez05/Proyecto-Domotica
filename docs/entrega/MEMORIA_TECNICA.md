# Memoria técnica — Proyecto Domótica (eficiencia energética en aula)

Documento de decisiones y justificaciones del desarrollo. Complementa [`../ARQUITECTURA_MEDALLION.md`](../ARQUITECTURA_MEDALLION.md) y [`../PROYECTO_ESTADO.md`](../PROYECTO_ESTADO.md). El umbral de ventilación para derroche se fija en **15 %** (`DERROCHE_VENTILATION_THRESHOLD_PCT` en `utils/config.py`).

---

## 1. Contexto y objetivo

El problema es el **derroche de calefacción** en un aula del centro: ventanas o puerta abiertas con la calefacción activa. No medimos el consumo eléctrico en kWh directamente; trabajamos con **series horarias** de sensores (Home Assistant / PostgreSQL, tabla `ltss`) y derivamos reglas de negocio y un **target de clasificación** para la **hora siguiente**.

**Objetivo de IA:** predecir si habrá **derroche en la siguiente hora** (`target_derroche_next_hour`), alineado con la definición operativa de derroche del proyecto (sección 2).

---

## 2. Definición de derroche (criterio único para el modelo)

Tras iterar el criterio con datos reales y normas de temperatura, el derroche en una hora `t` se define como:

1. **Calefacción considerada encendida** según las **normas de temperatura** aplicadas a la temperatura del **export History** (bronze), con tramos horarios laborables y histéresis (apagar/encender por umbrales). Esto se materializa en `calefaccion_on_normas_history` (`utils/heating_normas.py` + merge del CSV en `build_gold_dataset.py`).  
   Si no hubiera columna de normas History, el código puede usar `calefaccion_on_pred` (temperatura lineal / aula) como respaldo.

2. **Ventilación ponderada alta:** `porcentaje_ventilacion_aula` **estrictamente mayor que 15 %**.  
   Ese **15 %** es el umbral acordado para la entrega: concentra la idea de “demasiada apertura respecto al cómputo ponderado puerta/ventanas” sin fijar un único umbral en minutos absolutos, porque la métrica ya es un porcentaje respecto a un divisor total (`TOTAL_WEIGHT_DIVISOR = 20`).

**Fórmula lógica:** `derroche = (calefaccion_on_normas_history == 1) AND (porcentaje_ventilacion_aula > 15)`.

**Target:** `target_derroche_next_hour` = desplazamiento de `derroche` una hora hacia adelante (`shift(-1)`), de modo que las features de la hora actual explican el derroche de la hora siguiente.

**Justificación del 15 %:** Es un umbral explícito en código y documentación, revisable con negocio; separa situaciones de ventilación moderada de situaciones claramente incompatibles con calefacción encendida en el marco del proyecto.

---

## 3. Fuentes de datos

- **PostgreSQL / Timescale (operativa):** agregación horaria desde `ltss` (`queries/master_query.sql`): meteo, sol, aula, contactos de puerta/ventanas para la **ventilación ponderada**.

- **Bronze — History CSV:** temperatura (y humedad) horaria usada para **normas de calefacción** y para entrenar el modelo lineal de temperatura de referencia (`data/bronze/History_*.csv`, ruta por defecto en `utils/config.py`). El solapamiento temporal entre SQL y History no es total; donde no hay History, no hay `temperatura_history_calef` y la norma de calefacción no puede marcar encendido de la misma forma.

**Decisión:** Mantener una única query SQL como fuente de agregación horaria y enriquecer en Python con History para no duplicar lógica de negocio en dos sitios distintos sin control.

---

## 4. Ventilación ponderada (requisito del enunciado)

- Ventana **pequeña** (pares en la convención del proyecto): peso **1**.  
- Ventana **grande** (impares): peso **2**.  
- **Puerta:** peso **4** (equivalente a dos ventanas grandes en términos de peso).  
- **Divisor:** 20 — convierte el cómputo en un **porcentaje** comparable entre horas.

Implementación activa: `queries/master_query.sql` con constantes inyectadas desde `utils/config.py` en `build_gold_dataset.py`.

---

## 5. Arquitectura de datos (Medallion simplificada)

- **Bronze:** datos crudos o exportaciones (History).  
- **Gold:** `data/gold/master_dataset.csv` — tabla horaria única para análisis y features.  
- **Dataset IA:** `data/gold/dataset_final_ia.csv` — solo columnas de entrada + target para la red.

**Decisión:** Un solo archivo Gold evita bifurcaciones difíciles de reproducir; el export aplica el filtro de negocio (solo horas con calefacción encendida según normas History para entrenar el caso de uso “calefacción on”) y deja **NaN** en features donde falte meteo/aula para que el **imputer del entrenamiento** (fit solo en train) no duplique lógica con el CSV.

---

## 6. Modelos

### 6.1 Regresión lineal — temperatura de calefacción

**Script:** `scripts/train_linear_heating_model.py`.  
**Propósito:** estimar una temperatura de referencia (`temp_calefaccion_lineal`) útil para la columna `calefaccion_on_pred` (misma lógica de tramos que las normas History, pero con otra temperatura de entrada cuando procede).

**Justificación:** Modelo interpretable y ligero; encaja con el enunciado de modelo lineal y da continuidad con el resto del pipeline.

### 6.2 Red neuronal — derroche siguiente hora (Keras)

**Script:** `scripts/train_nn_derroche_model_keras.py`.  
**Entrada:** features numéricas con **codificación cíclica** de calendario: `hora_sin`/`hora_cos`, `dia_semana_sin`/`dia_semana_cos`, `mes_sin`/`mes_cos` (alineado con hora / día de la semana / mes del PDF), más sensores; imputación mediana y escalado **ajustados solo en train**, validación temporal interna, umbral en el joblib.

**Justificación:** Uso de **TensorFlow/Keras** alineado con la formación (MLP tabular), frente a un `MLPClassifier` previo archivado; separación clara entre preprocesado persistido y modelo para inferencia reproducible.

---

## 7. Inferencia y usabilidad

**Script:** `scripts/app_predict_derroche.py`.  
Se puede pasar **`--hora 0-23`** para no calcular a mano seno/coseno; el modelo sigue recibiendo las mismas features que en el CSV.

---

## 8. Informes y trazabilidad

- Métricas de modelos en `reports/`.  
- Informe HTML legible sobre Gold / dataset IA: `python scripts/generate_data_report.py` → `reports/informe_datos_gold.html`.  
- Auditoría de reproducibilidad: [`../../reports/AUDITORIA_REPRODUCIBILIDAD.md`](../../reports/AUDITORIA_REPRODUCIBILIDAD.md).

---

## 9. Entorno de ejecución respecto al PDF de asignatura

El documento de partida describe un despliegue concreto (p. ej. host de base de datos en la red del centro). El desarrollo y las pruebas se han hecho con **PostgreSQL local** y credenciales en **`.env`**, misma lógica SQL y mismos scripts. La memoria de entrega debe **explicitar** esta equivalencia funcional para el tribunal.

---

## 10. Limitaciones y trabajo pendiente fuera del núcleo ML

- **Dashboard Grafana** (visualizaciones + selector): pendiente de montar según especificación.  
- **Presentación** de cierre: material aparte.  
- Tamaño del dataset IA tras filtros estrictos: depende del solapamiento History–SQL y de la clase positiva; conviene reportar métricas y matriz de confusión en la defensa.

---

## 11. Referencias rápidas de archivos

| Elemento | Ubicación |
|-----------|-----------|
| Umbral 15 % y pesos | `utils/config.py` |
| Normas calefacción History | `utils/heating_normas.py` |
| Query horaria | `queries/master_query.sql` |
| Pipeline | `scripts/run_pipeline.py` |
| Artefactos NN | `models/nn_derroche_model_keras.keras`, `models/nn_derroche_preprocess_keras.joblib` |

---

*Última actualización coherente con el repositorio en la línea de desarrollo descrita en [`README.md`](../../README.md).*
