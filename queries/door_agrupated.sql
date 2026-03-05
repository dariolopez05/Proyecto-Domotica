WITH eventos AS (
    SELECT
        time,
        entity_id,
        state,
        LEAD(time) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_time,
        LEAD(state) OVER (
            PARTITION BY entity_id
            ORDER BY time
        ) AS next_state
    FROM ltss
    WHERE entity_id = 'binary_sensor.sensor_puerta_1_contact'
      AND state <> 'unavailable'
),
intervalos AS (
    SELECT
        entity_id,
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
        inicio,
        fin,
        generate_series(
            date_trunc('hour', inicio),
            date_trunc('hour', fin),
            interval '1 hour'
        ) AS hora
    FROM intervalos
)
SELECT
    hora,
    entity_id,
    SUM(
        LEAST(fin, hora + interval '1 hour')
        -
        GREATEST(inicio, hora)
    ) AS tiempo_on
FROM horas
GROUP BY hora, entity_id
ORDER BY hora;