-- Este script se ejecuta automáticamente al crear la base de datos por primera vez.
-- Su función es activar las extensiones necesarias para PostGIS y pgRouting.

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgrouting;
-- Crear tabla para almacenar metadatos de antenas
CREATE TABLE IF NOT EXISTS antenas (
    id SERIAL PRIMARY KEY,
    operador TEXT,
    tecnologia TEXT,
    geom GEOMETRY(Point, 4326) -- Usamos un tipo de dato geoespacial
);

-- Crear tabla para almacenar amenazas de Waze
CREATE TABLE IF NOT EXISTS amenazas_waze (
    id SERIAL PRIMARY KEY,
    waze_id TEXT UNIQUE,
    tipo_alerta TEXT,
    subtipo_alerta TEXT,
    descripcion TEXT,
    geom GEOMETRY(Point, 4326)
);

-- Crear tabla para almacenar antenas saturadas (penalización)
CREATE TABLE IF NOT EXISTS antenas_saturadas (
    id SERIAL PRIMARY KEY,
    id_antena TEXT,
    operador TEXT,
    comuna TEXT,
    geom GEOMETRY(Point, 4326)
);
