# Domótica — Proyecto de analítica/IA

Estructura base para un proyecto de ingesta, limpieza, feature engineering, modelado y reporting.

## Objetivos

¿Qué problema vais a resolver?
- El problema a resolver es el derroche energético en calefacción en el centro educativo por culpa de ventanas/puertas abiertas mientras la calefacción está encendida

¿Qué queréis predecir o detectar?
- El objetivo es usar los datos de temperatura que recogemos a lo largo de una hora para predecir si en la siguiente hora las ventanas van a ser abiertas o no

¿Cuál será el target del modelo?

# Indicaciones adicionales

- Los sensores de temperatura de las ventanas no hay que usarlos
- Hay que estudiar la correlacion entre los sensores para decidir con cual nos quedamos
- El csv con temperaturas mide las de un aula distinta a la nuestra en la misma orientación

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