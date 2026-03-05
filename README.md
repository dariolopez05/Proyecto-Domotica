# Domótica — Proyecto de analítica/IA

Estructura base para un proyecto de ingesta, limpieza, feature engineering, modelado y reporting.

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
├─ bi/
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
- Hay que estudiar la correlacion entre los sensores para decidir con cual nos quedamos o si hacemos una media de todo
- El csv con temperaturas mide las de un aula distinta a la nuestra en la misma ala del instituto
- Vamos a eliminar el sensor de la ventana 11 ya que dejó de funcionar en octubre de 2025 y proporciona lectura erroneas a partir de ese momento
- Las ventanas pares son las pequeñas (superiores), las grandes son las impares (inferiores) y vamos a tener en cuenta que cada ventana pequeña cuenta como 1 (unidad de medida mínima) con lo cual cada ventana grande cuenta como 2 

# Proceso de desarrollo

- Carga de datos en postgres con los scripts Creacion y Descarga
- Selección de las entity_ids que resultaban útiles para el problema a tratar
- Consulta SQL para extracción de atributos de la columna en formato Json (friendly_name, device_class y unit_of_measurement)
- Desarrollo de una consulta SQL para filtrar y agrupar por hora las entidades cuyo estado es cerrado (off) o abierto (on) sumando el tiempo total de apertura por hora, y después agrupando las entidades para obtener una suma del tiempo de apertura conjunto de todas las ventanas
- Desarrollo de una consulta SQL para filtrar y agrupar por hora las temperaturas de los sensores haciendo una media de sus valores