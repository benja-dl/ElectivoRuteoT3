#!/bin/bash

# --- CARGA DE DATOS CON osm2pgsql ---
echo "Cargando datos PBF a la base de datos PostGIS..."

docker-compose exec -T -e PGPASSWORD=tu_contraseña_segura app osm2pgsql \
    --create \
    -d tourdata_db \
    -U postgres \
    -H db \
    --slim \
    -C 2048 \
    /app/Infraestructura/region_data.osm.pbf

# --- CREACIÓN DE LA TOPOLOGÍA CON psql (VERSIÓN FINAL) ---
echo "Creando la topología de ruteo con pg_routing..."

docker-compose exec -T db psql -U postgres -d tourdata_db <<EOF
-- Nos aseguramos de que la extensión esté activa en esta sesión
CREATE EXTENSION IF NOT EXISTS pgrouting;

-- Añade una columna de ID secuencial
ALTER TABLE planet_osm_line ADD COLUMN gid SERIAL PRIMARY KEY;

-- Añadir columnas para la topología
ALTER TABLE planet_osm_line ADD COLUMN "source" integer;
ALTER TABLE planet_osm_line ADD COLUMN "target" integer;

-- Crear la topología usando la nueva columna 'gid'
SELECT pgr_createTopology('planet_osm_line', 0.00001, 'way', 'gid');
EOF

echo "Proceso de carga de infraestructura completado."
