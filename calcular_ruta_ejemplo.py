import os
import geopandas as gpd
from sqlalchemy import create_engine

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡¡¡CAMBIA ESTO!!!
DB_HOST = "db"
DB_PORT = "5432"

# --- PUNTOS DE ORIGEN Y DESTINO (Ejemplo sobre Ruta 5) ---
# Usaremos estos puntos que son un caso de prueba perfecto
start_lon, start_lat = -70.783, -33.284
end_lon, end_lat = -70.780, -33.315

try:
    engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')
    print("Conexión a la base de datos exitosa.")

    # --- CONSULTA SQL MEJORADA CON FILTRO DE CARRETERAS PRINCIPALES ---
    sql_query = f"""
        SELECT
            route.seq,
            ST_Transform(w.way, 4326) AS geometry
        FROM pgr_dijkstra(
            'SELECT gid AS id, source, target, ST_Length(way) AS cost FROM planet_osm_line WHERE highway IS NOT NULL',
            -- Subconsulta MEJORADA para encontrar el nodo de inicio
            (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
             JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
             WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
             ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({start_lon}, {start_lat}), 4326), 3857)
             LIMIT 1),
            -- Subconsulta MEJORADA para encontrar el nodo de fin
            (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
             JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
             WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
             ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({end_lon}, {end_lat}), 4326), 3857)
             LIMIT 1),
            directed := false
        ) AS route
        LEFT JOIN planet_osm_line w ON route.edge = w.gid;
    """

    print("Calculando la ruta de ejemplo (peor caso) con selección de nodo robusta...")
    route_gdf = gpd.read_postgis(sql_query, engine, geom_col='geometry')

    if not route_gdf.empty:
        route_gdf.set_crs("EPSG:4326", inplace=True)
        print(f"\n¡RUTA ENCONTRADA! Consta de {len(route_gdf)} segmentos.")

        output_folder = "SitioWeb"
        os.makedirs(output_folder, exist_ok=True)
        output_file = f"{output_folder}/ruta_ejemplo.geojson"

        route_gdf.to_file(output_file, driver="GeoJSON")
        print(f"\nRuta guardada en '{output_file}'.")
        print("Puedes visualizarla en https://geojson.io o en tu sitio web.")
    else:
        print("No se encontró una ruta entre los puntos seleccionados.")

except Exception as e:
    print(f"Ocurrió un error: {e}")

finally:
    if 'engine' in locals():
        engine.dispose()
        print("\nConexión cerrada.")
