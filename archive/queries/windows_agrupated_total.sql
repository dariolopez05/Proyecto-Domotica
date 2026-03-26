WITH eventos AS (
    SELECT
        time,
        entity_id,
        state,
        attributes,
        LEAD(time) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_time,
        LEAD(state) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_state
    FROM ltss
    WHERE entity_id IN (
        'binary_sensor.sensor_ventana_1_contact',
        'binary_sensor.sensor_ventana_2_contact',
        'binary_sensor.sensor_ventana_3_contact',
        'binary_sensor.sensor_ventana_4_contact',
        'binary_sensor.sensor_ventana_5_contact',
        'binary_sensor.sensor_ventana_6_contact',
        'binary_sensor.sensor_ventana_7_contact',
        'binary_sensor.sensor_ventana_8_contact',
        'binary_sensor.sensor_ventana_9_contact',
        'binary_sensor.sensor_ventana_10_contact',
        'binary_sensor.sensor_ventana_12_contact'
    )
    AND state <> 'unavailable'
),

intervalos AS (
    SELECT
        entity_id,
        attributes,
        time AS inicio,
        next_time AS fin
    FROM eventos
    WHERE state = 'on'
      AND next_state = 'off'
      AND next_time IS NOT NULL
),

horas AS (
    SELECT
        entity_id,
        attributes,
        generate_series(
            date_trunc('hour', inicio),
            date_trunc('hour', fin),
            interval '1 hour'
        ) AS hora,
        inicio,
        fin
    FROM intervalos
),

duracion_hora AS (
    SELECT
        hora,
        entity_id,
        attributes,
        -- Lógica de Peso: Extrae el número del ID. Si es impar -> peso 2, si es par -> peso 1.
        CASE 
            WHEN (substring(entity_id from 'ventana_([0-9]+)')::int % 2) <> 0 THEN 2 
            ELSE 1 
        END AS peso,
        EXTRACT(
            EPOCH FROM
            LEAST(fin, hora + interval '1 hour')
            -
            GREATEST(inicio, hora)
        ) AS segundos_abierto
    FROM horas
)

SELECT
    hora,
    entity_id,
    attributes->>'friendly_name' AS nombre,
    -- Tiempo real que ha estado abierta esta ventana
    SUM(segundos_abierto) * interval '1 second' AS tiempo_abierto,
    -- Tiempo ponderado (segundos * peso)
    SUM(segundos_abierto * peso) * interval '1 second' AS tiempo_ponderado,
    -- Ventilación total de la hora (Suma de todos los tiempos ponderados de todas las ventanas)
    SUM(SUM(segundos_abierto * peso)) OVER (PARTITION BY hora) * interval '1 second' AS total_ventilacion_ponderada_hora,
    -- Porcentaje de ventilación: (Total ponderado / (16 unidades * 3600 seg)) * 100
    ROUND(
        (SUM(SUM(segundos_abierto * peso)) OVER (PARTITION BY hora) / (16.0 * 3600.0)) * 100, 
        2
    ) AS porcentaje_ventilacion_aula
FROM duracion_hora
WHERE segundos_abierto > 0
GROUP BY hora, entity_id, attributes
ORDER BY porcentaje_ventilacion_aula desc, hora;