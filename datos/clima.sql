-- Extensión E3: no elimina ni modifica las tablas de E2.
CREATE SCHEMA IF NOT EXISTS ecotech;

CREATE TABLE IF NOT EXISTS ecotech.clima (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre TEXT NOT NULL CHECK (LENGTH(TRIM(nombre)) BETWEEN 1 AND 200),
    region TEXT NOT NULL CHECK (LENGTH(TRIM(region)) BETWEEN 1 AND 200),
    pais TEXT NOT NULL CHECK (LENGTH(TRIM(pais)) BETWEEN 1 AND 200),
    latitud NUMERIC(9, 6) NOT NULL CHECK (latitud BETWEEN -90 AND 90),
    longitud NUMERIC(9, 6) NOT NULL CHECK (longitud BETWEEN -180 AND 180),
    temperatura DOUBLE PRECISION NOT NULL
        CHECK (temperatura > '-Infinity'::DOUBLE PRECISION
            AND temperatura < 'Infinity'::DOUBLE PRECISION),
    humedad DOUBLE PRECISION NOT NULL CHECK (humedad BETWEEN 0 AND 100),
    codigo SMALLINT NOT NULL CHECK (codigo IN (
        0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57, 61, 63, 65,
        66, 67, 71, 73, 75, 77, 80, 81, 82, 85, 86, 95, 96, 99
    )),
    -- La petición meteorológica actual solicita siempre America/Santiago.
    fecha_clima TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    zona_horaria TEXT NOT NULL DEFAULT 'America/Santiago'
        CHECK (zona_horaria = 'America/Santiago'),
    obtenido_en TIMESTAMPTZ NOT NULL,
    UNIQUE (latitud, longitud, fecha_clima)
);

ALTER TABLE ecotech.clima ENABLE ROW LEVEL SECURITY;
