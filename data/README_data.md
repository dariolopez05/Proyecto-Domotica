# Datos (`data/`)

Estructura de datos por capas (tipo medallón).

- `bronze/`: datos crudos tal cual llegan (raw).
- `silver/`: datos limpios y normalizados (granularidad original).
- `gold/`: datos agregados / features listos para analítica e IA (por ejemplo, por hora).

Recomendación: si `bronze/` contiene datos sensibles o pesados, ignóralo en git.

