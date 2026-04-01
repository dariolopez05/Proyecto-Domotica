# Domótica — Proyecto de analítica/IA

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

## App web — Predicción interactiva

Interfaz visual para introducir los parámetros manualmente y obtener la predicción del modelo.

### Requisitos previos

Necesitas **Python 3.12** (TensorFlow no soporta Python 3.14+). Instálalo desde la Microsoft Store buscando "Python 3.12" o con:

```bash
winget install Python.Python.3.12
```

### Instalación de dependencias (solo la primera vez)

```bash
py -3.12 -m pip install tensorflow-cpu flask joblib pandas numpy scikit-learn==1.7.2
```

> La versión exacta `scikit-learn==1.7.2` es necesaria para cargar el preprocesador guardado con el modelo.

### Arrancar el servidor

```bash
py -3.12 web_app/app.py
```

Abre el navegador en **http://localhost:5000**

### Uso

1. Ajusta la **hora** (0–23) con el slider — se convierte automáticamente a sin/cos
2. Rellena el resto de parámetros con los sliders o escribiendo el valor directamente
3. Pulsa **Ejecutar análisis predictivo**
4. El panel derecho muestra la probabilidad de derroche en la siguiente hora y el veredicto

---

## Pipeline operativo

Ejecutar extremo a extremo:

```bash
python scripts/run_pipeline.py
```

Pasos internos:
1. Construcción Gold (`build_gold_dataset.py`)
2. Entrenamiento lineal calefacción (`train_linear_heating_model.py`)
3. Rebuild Gold con columna lineal
4. Export dataset final IA (`export_final_ia_dataset.py`)
5. Entrenamiento red neuronal (Keras) (`train_nn_derroche_model_keras.py`)

## Objetivos

¿Qué problema vais a resolver?
- El problema a resolver es el derroche energético en calefacción en el centro educativo por culpa de ventanas/puertas abiertas mientras la calefacción está encendida

¿Qué queréis predecir o detectar?
- El objetivo es usar los datos de temperatura que recogemos a lo largo de una hora para predecir si en la siguiente hora las ventanas van a ser abiertas o no

¿Cuál será el target del modelo?

## Estructura

```text
Domotica/
├─ README.md
├─ .gitignore
├─ .gitattributes
├─ docs/
│  ├─ README.md
│  ├─ memoria_tecnica.pdf          # colocar aquí (no se genera automáticamente)
│  ├─ decisiones_arquitectura.md
│  └─ anexos/
│     └─ README.md
├─ presentacion/
│  └─ README.md                    # colocar aquí la presentación final (PDF/PPTX)
├─ archive/bi/                      # opcional (Power BI, archivado)
│  ├─ README.md                    # dashboard + notas
│  ├─ dashboard.pbix               # opcional (Power BI)
│  └─ assets/
│     └─ .gitkeep
├─ datasets/
│  ├─ README_datasets.md
│  ├─ raw/                         # ingesta tal cual llega (normalmente ignorado en git)
│  │  └─ .gitkeep
│  ├─ cleaned/                     # limpio/normalizado (granularidad original)
│  │  └─ .gitkeep
│  └─ curated/                     # features/tabla final (p.ej. por hora)
│     └─ .gitkeep
├─ pipelines/
│  ├─ README.md
│  └─ sql/
│     ├─ 10_ingesta_raw.sql
│     ├─ 20_limpieza_cleaned.sql
│     └─ 30_features_curated_hourly.sql
├─ notebooks/
│  └─ README.md                    # lista de notebooks y propósito
├─ src/
│  └─ README.md                    # código reusable (ETL/features/modelos)
├─ artifacts/
│  ├─ README.md
│  ├─ models/
│  │  └─ .gitkeep
│  └─ reports/
│     └─ metrics.json
└─ requirements.txt                # opcional (si usas Python)
```

## Notas

- Si vas a versionar datos, hazlo solo en `datasets/cleaned` o `datasets/curated` y siempre sin información sensible.
- Los binarios pesados (PBIX, PDFs, modelos) pueden mantenerse en el repo si el tamaño lo permite, o gestionarse con releases/almacenamiento externo.

# Indicaciones adicionales

- Los sensores de temperatura de las ventanas no hay que usarlos
- Buscar el coeficiente de correlacion entre los 4 sensores de temperatura internos para decidir con cual nos quedamos
- El csv con temperaturas mide las de un aula distinta a la nuestra en la misma ala del instituto
- Vamos a eliminar el sensor de la ventana 11 ya que dejó de funcionar en octubre de 2025 y proporciona lectura erroneas a partir de ese momento
- Las ventanas pares son las pequeñas (superiores), las grandes son las impares (inferiores) y vamos a tener en cuenta que cada ventana pequeña cuenta como 1 (unidad de medida mínima) con lo cual cada ventana grande cuenta como 2

# Proceso de desarrollo
### Carga y filtrado de datos
- Carga de datos en postgres con los scripts Creacion y Descarga
- Selección de las entity_ids que resultaban útiles para el problema a tratar
- Consulta SQL para extracción de atributos de la columna en formato Json (friendly_name, device_class y unit_of_measurement)

### Cálculo de tiempo de apertura
- Desarrollo de una consulta SQL para filtrar y agrupar por hora las entidades cuyo estado es cerrado (off) o abierto (on) sumando el tiempo total de apertura por hora, y después agrupando las entidades con una funcion ventana para obtener una suma del tiempo de apertura conjunto de todas las ventanas

### Cálculo de temperaturas
- Desarrollo de una consulta SQL para filtrar y agrupar por hora las temperaturas y humedad de los sensores haciendo una media de sus valores

### Selección de sensores
- Desarrollo de un script python para calcular la correlacion entre los diferentes sensores de temperatura del aula y sus gráficos asociados.

- El diagnóstico final ha sido mantener unicamente el sensor 4 (centro del aula), ya que los sensores 2 (ventana) y 3 (puerta) sufrian variaciones de temperatura ligeramente más marcadas debido a la apertura de las mismas y el sensor 1 (esquina) tenía una correlación del 99.9% con el central, con lo cual ofrecía información redundante

### Regresión de Temperatura
- Desarrollar un modelo de regresion lineal para predecir la temperatura de la calefacción (que decide si está encendida o no) para averiguar según el algoritmo de encendido/apagado el estado actual de la calefacción

### Sensores/Agrupaciones
temperatura-media
humedad-media
nubosidad-media
presión-media
viento-moda
dirección viento-moda
azimuth solar-mediana
elevación solar-mediana
forecast-último valor

# To-Do list
- Refactor del script de correlacion de sensores para automatizar la creacion de csv mediante consulta sql "media_temperature"
- Explorar métodos de automatización de limpieza de datos con python, posible cambio a python o integración con los sql existentes