CREATE TABLE IF NOT EXISTS ecotech.medicion_calidad_aire (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    pm2_5 NUMERIC(10, 3) NOT NULL CHECK (pm2_5 >= 0),
    pm10 NUMERIC(10, 3) NOT NULL CHECK (pm10 >= 0),
    us_aqi INTEGER NOT NULL CHECK (us_aqi BETWEEN 0 AND 500),
    fecha_hora TIMESTAMPTZ NOT NULL,
    latitud NUMERIC(9, 6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9, 6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    obtenido_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE ecotech.medicion_calidad_aire
ENABLE ROW LEVEL SECURITY;

-- Evita registrar dos veces la misma observación
-- para una misma ubicación.
CREATE UNIQUE INDEX IF NOT EXISTS uq_medicion_calidad_aire_observacion
ON ecotech.medicion_calidad_aire (
    fecha_hora,
    latitud,
    longitud
);
