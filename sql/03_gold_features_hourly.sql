-- 03_gold_features_hourly.sql
-- Objetivo: construir features agregadas (p.ej. por hora) en la capa GOLD.

/* Ejemplo (placeholder)
-- CREATE TABLE gold_features_hourly AS
-- SELECT
--   sensor_id,
--   DATE_TRUNC('hour', timestamp_utc) AS hour_ts,
--   AVG(valor) AS avg_valor,
--   MIN(valor) AS min_valor,
--   MAX(valor) AS max_valor,
--   COUNT(*)  AS n
-- FROM silver_sensores
-- GROUP BY sensor_id, DATE_TRUNC('hour', timestamp_utc);
*/

