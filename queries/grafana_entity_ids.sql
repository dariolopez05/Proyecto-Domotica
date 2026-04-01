-- Lista de entity_id usada en Grafana (dashboard domotica-temperatura) y en queries/entity_ids_listed.sql.
-- Mantener sincronizado con entity_ids_listed.sql (mismo IN).

-- Subconjunto solo numéricos (líneas en la vista "Todos numéricos juntos"):
--   sensor.mislata_direccion_viento, sensor.mislata_humedad, sensor.mislata_nubosidad,
--   sensor.mislata_presion, sensor.mislata_temperatura, sensor.mislata_viento,
--   sensor.sensor_temperatura_4_humidity, sensor.sensor_temperatura_4_pressure,
--   sensor.sensor_temperatura_4_temperature, sensor.sun_solar_azimuth, sensor.sun_solar_elevation
-- (excluye binarios, weather.forecast_mislata y textos no numéricos.)

-- Para la variable "sensor" en Grafana (desplegable):
SELECT entity_id FROM (
  VALUES
    ('binary_sensor.sensor_puerta_1_contact'),
    ('binary_sensor.sensor_ventana_1_contact'),
    ('binary_sensor.sensor_ventana_2_contact'),
    ('binary_sensor.sensor_ventana_3_contact'),
    ('binary_sensor.sensor_ventana_4_contact'),
    ('binary_sensor.sensor_ventana_5_contact'),
    ('binary_sensor.sensor_ventana_6_contact'),
    ('binary_sensor.sensor_ventana_7_contact'),
    ('binary_sensor.sensor_ventana_8_contact'),
    ('binary_sensor.sensor_ventana_9_contact'),
    ('binary_sensor.sensor_ventana_10_contact'),
    ('binary_sensor.sensor_ventana_12_contact'),
    ('sensor.mislata_direccion_viento'),
    ('sensor.mislata_humedad'),
    ('sensor.mislata_nubosidad'),
    ('sensor.mislata_presion'),
    ('sensor.mislata_temperatura'),
    ('sensor.mislata_viento'),
    ('sensor.sensor_temperatura_4_humidity'),
    ('sensor.sensor_temperatura_4_pressure'),
    ('sensor.sensor_temperatura_4_temperature'),
    ('sensor.sun_solar_azimuth'),
    ('sensor.sun_solar_elevation'),
    ('weather.forecast_mislata')
) AS t(entity_id)
ORDER BY 1;
