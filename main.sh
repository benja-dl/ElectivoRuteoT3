#!/bin/bash
# --------------------------------------------------
# SCRIPT DE AUTOMATIZACIÓN TOTAL - TOURDATA CONNECT (FINAL)
# --------------------------------------------------

echo "--- [INICIO] PROCESO DE AUTOMATIZACIÓN DE TOURDATA CONNECT ---"

# --- 1. LIMPIEZA Y CONSTRUCCIÓN DEL ENTORNO ---
echo -e "\n[PASO 1/7] Limpiando entorno Docker anterior (borrando volúmenes)..."
docker-compose down -v

echo -e "\n[PASO 2/7] Construyendo y levantando contenedores (Base de Datos y API Flask)..."
# El 'command: python3 /app/api.py' en docker-compose.yml iniciará el servidor aquí.
docker-compose up --build -d

echo "[PASO 3/7] Esperando 30 segundos a que la Base de Datos se inicialice..."
sleep 30

# --- 2. ETL DE INFRAESTRUCTURA (CALLES Y RUTAS) ---
echo -e "\n[PASO 4/7] Ejecutando ETL de Infraestructura (OpenStreetMap)..."

echo "  (4a) Descargando archivo .pbf de Chile..."
docker-compose exec app wget --user-agent="Mozilla/5.0" "http://download.geofabrik.de/south-america/chile-latest.osm.pbf" -O Infraestructura/region_data.osm.pbf

echo "  (4b) Cargando .pbf a PostGIS y creando topología (esto tardará varios minutos)..."
# Damos permisos de ejecución por si acaso
chmod +x ./Infraestructura/load_to_db.sh
./Infraestructura/load_to_db.sh

# --- 3. ETL DE METADATOS Y AMENAZAS ---
echo -e "\n[PASO 5/7] Ejecutando ETL de Metadatos y Amenazas..."

echo "  (5a) Transformando Antenas en Servicio (CSV a GeoJSON)..."
docker-compose exec app python3 Metadata/extract_transform_antenas.py
echo "  (5b) Cargando Antenas en Servicio a la BD..."
docker-compose exec app python3 Metadata/load_antenas_to_db.py

echo "  (5c) Transformando Antenas Saturadas (CSV a GeoJSON)..."
docker-compose exec app python3 Metadata/extract_transform_saturadas.py
echo "  (5d) Cargando Antenas Saturadas a la BD..."
docker-compose exec app python3 Metadata/load_saturadas_to_db.py

echo "  (5e) Extrayendo alertas en tiempo real de Waze..."
docker-compose exec app python3 Amenazas/extract_transform_waze.py
echo "  (5f) Cargando alertas de Waze a la BD..."
docker-compose exec app python3 Amenazas/load_waze_to_db.py

# --- 4. MODELADO DE COSTOS (¡Paso Crítico!) ---
echo -e "\n[PASO 6/7] Modelando costos de red (Probabilidad de Falla y Costo Resiliente)..."
docker-compose exec app python3 Modelado/modelar_costos.py

# --- 5. RUTA DE EJEMPLO Y LANZAMIENTO ---
echo -e "\n[PASO 7/7] Generando ruta de ejemplo (Peor Caso) para el inicio..."
docker-compose exec app python3 calcular_ruta_ejemplo.py

echo -e "\n--- [¡AUTOMATIZACIÓN COMPLETADA!] ---"
echo "Tu API de Flask y tu sitio web ya están corriendo en http://localhost:8000"
echo "Mostrando los logs del servidor (presiona Ctrl+C para salir):"

# El servidor API ya está corriendo gracias a docker-compose.
# Este comando solo se conecta a los logs para que puedas ver la actividad.
docker-compose logs -f app
