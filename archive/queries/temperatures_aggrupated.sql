SELECT 
    date_trunc('hour', time) AS hora,
    -- Lista de sensores que han contribuido en esta hora (sin duplicados)
    string_agg(DISTINCT entity_id, ', ') AS entidades,
    -- Media de temperatura
    ROUND(AVG(state::numeric), 2) AS temperatura_media,
    -- Metadatos de la muestra
    COUNT(*) AS total_lecturas,
    COUNT(DISTINCT entity_id) AS total_sensores_distintos
FROM ltss
WHERE 
    (entity_id LIKE 'sensor.sensor_temperatura_%_temperature' 
     OR entity_id = 'sensor.mislata_temperatura')
    AND state NOT IN ('unavailable', 'unknown', 'none')
    AND state ~ '^-?[0-9]+(\.[0-9]+)?$' 
GROUP BY hora
ORDER BY hora DESC;