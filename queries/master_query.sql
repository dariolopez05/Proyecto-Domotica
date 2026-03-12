SELECT
    date_trunc('hour', time) AS datetime,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.mislata_temperatura'
    ),2) AS temperatura_exterior,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.mislata_humedad'
    ),2) AS humedad_exterior,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.mislata_presion'
    ),2) AS presion,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.mislata_nubosidad'
    ),2) AS nubosidad,

    ROUND(
        (mode() WITHIN GROUP (ORDER BY state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_viento'
        ))::numeric,2
    ) AS viento,

    ROUND(
        (mode() WITHIN GROUP (ORDER BY state::numeric) FILTER (
            WHERE entity_id = 'sensor.mislata_direccion_viento'
        ))::numeric,2
    ) AS direccion_viento,

    ROUND(
        (percentile_cont(0.5) WITHIN GROUP (ORDER BY state::numeric)
        FILTER (WHERE entity_id = 'sensor.sun_solar_azimuth'))::numeric,2
    ) AS azimuth_sol,

    ROUND(
        (percentile_cont(0.5) WITHIN GROUP (ORDER BY state::numeric)
        FILTER (WHERE entity_id = 'sensor.sun_solar_elevation'))::numeric,2
    ) AS elevacion_sol,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.sensor_temperatura_4_temperature'
    ),2) AS temperatura_aula,

    ROUND(AVG(state::numeric) FILTER (
        WHERE entity_id = 'sensor.sensor_temperatura_4_humidity'
    ),2) AS humedad_aula,

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
ORDER BY datetime;