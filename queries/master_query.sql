WITH master_hourly AS (
    SELECT
        date_trunc('hour', time) AS datetime,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_temperatura'
        ), 2) AS temperatura_exterior,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_humedad'
        ), 2) AS humedad_exterior,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_presion'
        ), 2) AS presion,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_nubosidad'
        ), 2) AS nubosidad,
        ROUND(
            (mode() WITHIN GROUP (ORDER BY state::numeric) FILTER (
                WHERE entity_id = 'sensor.mislata_viento'
            ))::numeric, 2
        ) AS viento,
        ROUND(
            (mode() WITHIN GROUP (ORDER BY state::numeric) FILTER (
                WHERE entity_id = 'sensor.mislata_direccion_viento'
            ))::numeric, 2
        ) AS direccion_viento,
        ROUND(
            (percentile_cont(0.5) WITHIN GROUP (ORDER BY state::numeric)
            FILTER (WHERE entity_id = 'sensor.sun_solar_azimuth'))::numeric, 2
        ) AS azimuth_sol,
        ROUND(
            (percentile_cont(0.5) WITHIN GROUP (ORDER BY state::numeric)
            FILTER (WHERE entity_id = 'sensor.sun_solar_elevation'))::numeric, 2
        ) AS elevacion_sol,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.sensor_temperatura_4_temperature'
        ), 2) AS temperatura_aula,
        ROUND(AVG(state::numeric) FILTER (
            WHERE entity_id = 'sensor.sensor_temperatura_4_humidity'
        ), 2) AS humedad_aula,
        MAX(state) FILTER (
            WHERE entity_id = 'weather.forecast_mislata'
        ) AS forecast
    FROM ltss
    WHERE entity_id IN (
        'sensor.sun_solar_azimuth',
        'sensor.sun_solar_elevation',
        'weather.forecast_mislata',
        'sensor.mislata_direccion_viento',
        'sensor.mislata_humedad',
        'sensor.mislata_nubosidad',
        'sensor.mislata_presion',
        'sensor.mislata_temperatura',
        'sensor.mislata_viento',
        'sensor.sensor_temperatura_4_temperature',
        'sensor.sensor_temperatura_4_humidity'
    )
      AND state <> 'unavailable'
    GROUP BY datetime
),
eventos AS (
    SELECT
        time,
        entity_id,
        state,
        LEAD(time) OVER (PARTITION BY entity_id ORDER BY time) AS next_time,
        LEAD(state) OVER (PARTITION BY entity_id ORDER BY time) AS next_state
    FROM ltss
    WHERE entity_id IN (
        'binary_sensor.sensor_puerta_1_contact',
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
        CASE
            WHEN entity_id = 'binary_sensor.sensor_puerta_1_contact' THEN {{DOOR_WEIGHT}}
            WHEN (substring(entity_id from 'ventana_([0-9]+)')::int % 2) <> 0 THEN {{WINDOW_WEIGHT_LARGE}}
            ELSE {{WINDOW_WEIGHT_SMALL}}
        END AS peso,
        EXTRACT(
            EPOCH FROM
            LEAST(fin, hora + interval '1 hour')
            - GREATEST(inicio, hora)
        ) AS segundos_abierto
    FROM horas
),
ventilacion_por_hora AS (
    SELECT
        hora AS datetime,
        ROUND(SUM(segundos_abierto * peso) / 60.0, 2) AS total_ventilacion_ponderada_min,
        ROUND((SUM(segundos_abierto * peso) / ({{TOTAL_WEIGHT_DIVISOR}}::numeric * 3600.0)) * 100, 2) AS porcentaje_ventilacion_aula
    FROM duracion_hora
    WHERE segundos_abierto > 0
    GROUP BY hora
)
SELECT
    m.*,
    COALESCE(v.total_ventilacion_ponderada_min, 0.0) AS total_ventilacion_ponderada_min,
    COALESCE(v.porcentaje_ventilacion_aula, 0.0) AS porcentaje_ventilacion_aula
FROM master_hourly m
LEFT JOIN ventilacion_por_hora v ON m.datetime = v.datetime
ORDER BY m.datetime;