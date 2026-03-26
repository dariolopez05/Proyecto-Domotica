SELECT
    date_trunc('hour', time) AS hora,
    entity_id,
    attributes->>'friendly_name' AS nombre,
    AVG(state::numeric) AS media_valor,
    attributes->>'device_class' AS dispositivo,
    attributes->>'unit_of_measurement' AS unidad
FROM ltss
WHERE entity_id IN (
'sensor.sensor_temperatura_4_temperature',
'sensor.sensor_temperatura_4_humidity'
)
AND state <> 'unavailable'
GROUP BY hora, entity_id, nombre, dispositivo, unidad
ORDER BY hora, entity_id;