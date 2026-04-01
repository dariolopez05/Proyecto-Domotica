# Grafana — dashboard temperatura (Fase D)

Cumple el mínimo del PDF: **dos visualizaciones** (serie temporal + gauge de media) y **variable** para elegir el sensor de temperatura. Los paneles leen la tabla **`ltss`** del mismo PostgreSQL que usa `queries/master_query.sql`.

La capa Gold (`data/gold/master_dataset.csv`) se genera con el pipeline Python; **no hace falta ninguna tabla extra en PostgreSQL** para este dashboard.

## Requisitos

- Docker (Docker Desktop en Windows está bien).
- PostgreSQL accesible con la tabla `ltss` y credenciales en el `.env` **del directorio raíz del repo** (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`).

## Arranque rápido

Desde esta carpeta (`grafana/`):

```bash
docker compose up -d
```

Abre **http://localhost:3000** — credenciales según `docker-compose.yml`.

El dashboard provisionado es **Domótica — temperatura (LTSS)** (`dashboards/domotica-temperatura.json`, UID `domotica-temp`).

## Conectar Grafana (en Docker) con PostgreSQL en tu PC

Si la base está en `localhost` del anfitrión y Grafana corre en contenedor:

1. En el `.env` del repo, pon **`DB_HOST=host.docker.internal`** (Windows/Mac; en Linux suele usarse la IP del bridge o `network_mode: host`).
2. Asegúrate de que PostgreSQL acepta conexiones desde Docker (firewall / `listen_addresses`).

Si PostgreSQL y Grafana están en la misma red (p. ej. servidor del centro), usa el **host real** en `.env`, igual que para los scripts Python.

## Qué hace el dashboard

| Elemento | Descripción |
|----------|-------------|
| **Variable "Sensor de temperatura"** | Solo **aula** (`sensor.sensor_temperatura_4_temperature`) y **exterior Mislata** (`sensor.mislata_temperatura`), alineado con `queries/master_query.sql`. Para ampliar la lista, edita la consulta de la variable en `dashboards/domotica-temperatura.json` (templating → `sensor`). |
| **Paneles** | Serie temporal, KPIs (última, mín, máx, lecturas) y gauge de media en el rango de fechas. |

El dashboard trae por defecto el rango de mediciones del proyecto (**2024-12-18 18:06:21** → **2026-03-02 08:39:21**); puedes cambiarlo arriba a la derecha si hace falta.

## No se ven datos en los paneles

1. **Rango de fechas**: amplía el intervalo o usa **Absolute time range**; los datos históricos pueden ser de otro año (p. ej. 2024).
2. **Sensor**: el desplegable debe tener un `entity_id` válido.
3. **Explore**: `SELECT min("time"), max("time"), count(*) FROM public.ltss WHERE entity_id = 'sensor.mislata_temperatura';` (ajusta el `entity_id`).

## Sin Docker (import manual)

1. Instala Grafana en tu sistema.
2. Crea un datasource **PostgreSQL** con los mismos datos que `.env` (SSL mode *disable* si es local sin TLS).
3. **Import** → sube `dashboards/domotica-temperatura.json` y elige el datasource PostgreSQL.

## Archivos

- `docker-compose.yml` — servicio Grafana + provisioning.
- `provisioning/datasources/postgres.yml` — datasource (`${DB_HOST}`, etc.).
- `provisioning/dashboards/default.yml` — carga JSON de `dashboards/`.
- `dashboards/domotica-temperatura.json` — definición del dashboard (Fase D).
