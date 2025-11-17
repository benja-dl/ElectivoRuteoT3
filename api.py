from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy import create_engine, text
import json
import time
import random

# --- CONFIGURACIÓN DE LA APP FLASK ---
app = Flask(__name__)

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡CAMBIA ESTO!
DB_HOST = "db"
DB_PORT = "5432"
    
db_url = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)

# --- RUTA DE LA API PARA CALCULAR RUTAS (PEOR CASO) ---
@app.route('/api/calculate_route', methods=['POST'])
def calculate_route():
    data = request.json
    print(f"Recibida solicitud de ruta: {data}")

    try:
        start_lat = float(data['start']['lat'])
        start_lon = float(data['start']['lon'])
        end_lat = float(data['end']['lat'])
        end_lon = float(data['end']['lon'])

        sql_query = text(f"""
            SELECT row_to_json(fc)
            FROM (
                SELECT 'FeatureCollection' AS type, array_to_json(array_agg(f)) AS features
                FROM (
                    SELECT 'Feature' AS type,
                    ST_AsGeoJSON(ST_Transform(w.way, 4326))::json AS geometry,
                    json_build_object('id', route.edge, 'cost', route.cost) AS properties
                    FROM pgr_dijkstra(
                        'SELECT gid AS id, source, target, ST_Length(way) AS cost FROM planet_osm_line WHERE highway IS NOT NULL AND highway != ''ferry''',
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({start_lon}, {start_lat}), 4326), 3857)
                         LIMIT 1),
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({end_lon}, {end_lat}), 4326), 3857)
                         LIMIT 1),
                        directed := false
                    ) AS route
                    LEFT JOIN planet_osm_line w ON route.edge = w.gid
                ) AS f
            ) AS fc;
        """)

        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute(sql_query).fetchone()
            end_time = time.time()
            compute_time = (end_time - start_time) * 1000
            
            if result and result[0]:
                geojson_data = result[0]
                geojson_data['properties'] = {'compute_time_ms': compute_time}
                return geojson_data, 200
            else:
                return jsonify({"error": "No se encontró una ruta."}), 404
        
    except Exception as e:
        print(f"Error en el cálculo de ruta: {e}")
        return jsonify({"error": str(e)}), 500

# --- RUTA DE LA API PARA CALCULAR LA RUTA RESILIENTE ---
@app.route('/api/calculate_resilient_route', methods=['POST'])
def calculate_resilient_route():
    data = request.json
    print(f"Recibida solicitud de ruta RESILIENTE: {data}")

    try:
        start_lat = float(data['start']['lat'])
        start_lon = float(data['start']['lon'])
        end_lat = float(data['end']['lat'])
        end_lon = float(data['end']['lon'])

        sql_query = text(f"""
            SELECT row_to_json(fc)
            FROM (
                SELECT 'FeatureCollection' AS type, array_to_json(array_agg(f)) AS features
                FROM (
                    SELECT 'Feature' AS type,
                    ST_AsGeoJSON(ST_Transform(w.way, 4326))::json AS geometry,
                    json_build_object('id', route.edge, 'cost', route.cost) AS properties
                    FROM pgr_dijkstra(
                        'SELECT gid AS id, source, target, cost_resiliente AS cost FROM planet_osm_line WHERE highway IS NOT NULL AND cost_resiliente > 0 AND highway != ''ferry''',
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({start_lon}, {start_lat}), 4326), 3857)
                         LIMIT 1),
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({end_lon}, {end_lat}), 4326), 3857)
                         LIMIT 1),
                        directed := false
                    ) AS route
                    LEFT JOIN planet_osm_line w ON route.edge = w.gid
                ) AS f
            ) AS fc;
        """)

        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute(sql_query).fetchone()
            end_time = time.time()
            compute_time = (end_time - start_time) * 1000
            
            if result and result[0]:
                geojson_data = result[0]
                geojson_data['properties'] = {'compute_time_ms': compute_time}
                return geojson_data, 200
            else:
                return jsonify({"error": "No se encontró una ruta resiliente."}), 404
        
    except Exception as e:
        print(f"Error en el cálculo de ruta resiliente: {e}")
        return jsonify({"error": str(e)}), 500

# --- RUTA DE LA API PARA SIMULAR FALLAS (REQUISITO #6) ---
@app.route('/api/simulate_failures', methods=['GET'])
def simulate_failures():
    print("Recibida solicitud de simulación de fallas...")
    try:
        sql_query = text("""
            SELECT 
                gid, 
                prob_falla, 
                ST_AsGeoJSON(ST_Transform(way, 4326))::json AS geometry
            FROM 
                planet_osm_line
            WHERE 
                prob_falla > 0
                AND highway != 'ferry';
        """)

        failed_links_features = []
        
        with engine.connect() as connection:
            potential_failures = connection.execute(sql_query).fetchall()
            print(f"Evaluando {len(potential_failures)} enlaces con probabilidad de falla...")

            for link in potential_failures:
                gid, prob_falla, geometry = link
                roll = random.random()
                
                if roll < prob_falla:
                    failed_links_features.append({
                        "type": "Feature",
                        "geometry": geometry,
                        "properties": { "gid": gid, "prob_falla": prob_falla, "roll": roll }
                    })

        geojson_response = {
            "type": "FeatureCollection",
            "features": failed_links_features
        }
        
        print(f"Simulación completada. {len(failed_links_features)} enlaces fallaron.")
        return jsonify(geojson_response), 200

    except Exception as e:
        print(f"Error en la simulación de fallas: {e}")
        return jsonify({"error": str(e)}), 500

# --- RUTA DE LA API PARA RUTA DE CONTINGENCIA (EVITANDO FALLAS) ---
@app.route('/api/calculate_contingency_route', methods=['POST'])
def calculate_contingency_route():
    data = request.json
    print(f"Recibida solicitud de ruta de CONTINGENCIA: {data}")

    try:
        start_lat = float(data['start']['lat'])
        start_lon = float(data['start']['lon'])
        end_lat = float(data['end']['lat'])
        end_lon = float(data['end']['lon'])
        
        failed_gids = data.get('failed_gids', [])
        
        exclude_condition = "AND 1=1"
        failed_gids_str = "NULL"
        if failed_gids:
            failed_gids_str = str(tuple(failed_gids))
            if len(failed_gids) == 1:
                failed_gids_str = failed_gids_str.replace(',', '')
            exclude_condition = f"AND gid NOT IN {failed_gids_str}"

        # Consulta SQL corregida para excluir nodos de inicio/fin de calles fallidas
        sql_query = text(f"""
            SELECT row_to_json(fc)
            FROM (
                SELECT 'FeatureCollection' AS type, array_to_json(array_agg(f)) AS features
                FROM (
                    SELECT 'Feature' AS type,
                    ST_AsGeoJSON(ST_Transform(w.way, 4326))::json AS geometry,
                    json_build_object('id', route.edge, 'cost', route.cost) AS properties
                    FROM pgr_dijkstra(
                        'SELECT gid AS id, source, target, cost_resiliente AS cost 
                         FROM planet_osm_line 
                         WHERE highway IS NOT NULL AND cost_resiliente > 0 {exclude_condition} AND highway != ''ferry''',
                        
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         AND l.gid NOT IN {failed_gids_str}
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({start_lon}, {start_lat}), 4326), 3857)
                         LIMIT 1),
                        (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                         JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                         WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                         AND l.gid NOT IN {failed_gids_str}
                         ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({end_lon}, {end_lat}), 4326), 3857)
                         LIMIT 1),
                        directed := false
                    ) AS route
                    LEFT JOIN planet_osm_line w ON route.edge = w.gid
                ) AS f
            ) AS fc;
        """)

        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute(sql_query).fetchone()
            end_time = time.time()
            compute_time = (end_time - start_time) * 1000

            if result and result[0]:
                geojson_data = result[0]
                geojson_data['properties'] = {'compute_time_ms': compute_time}
                return geojson_data, 200
            else:
                return jsonify({"error": "No se encontró una ruta de contingencia."}), 404

    except Exception as e:
        print(f"Error en el cálculo de ruta de contingencia: {e}")
        return jsonify({"error": str(e)}), 500

# --- RUTA DE LA API PARA k-Shortest Path (REQUISITO #5d) ---
@app.route('/api/calculate_ksp_route', methods=['POST'])
def calculate_ksp_route():
    data = request.json
    print(f"Recibida solicitud de ruta k-Shortest Path (kSP): {data}")

    try:
        start_lat = float(data['start']['lat'])
        start_lon = float(data['start']['lon'])
        end_lat = float(data['end']['lat'])
        end_lon = float(data['end']['lon'])
        
        k = 3

        sql_query = text(f"""
            WITH ksp AS (
                SELECT
                    route.path_seq,
                    route.edge,
                    route.cost,
                    w.way
                FROM pgr_kSP(
                    'SELECT gid AS id, source, target, cost_resiliente AS cost 
                     FROM planet_osm_line 
                     WHERE highway IS NOT NULL AND cost_resiliente > 0 AND highway != ''ferry''',
                    (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                     JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                     WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                     ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({start_lon}, {start_lat}), 4326), 3857)
                     LIMIT 1),
                    (SELECT v.id FROM planet_osm_line_vertices_pgr AS v
                     JOIN planet_osm_line AS l ON v.id = l.source OR v.id = l.target
                     WHERE l.highway IN ('motorway', 'trunk', 'primary', 'secondary', 'tertiary')
                     ORDER BY v.the_geom <-> ST_Transform(ST_SetSRID(ST_MakePoint({end_lon}, {end_lat}), 4326), 3857)
                     LIMIT 1),
                    {k},
                    directed := false
                ) AS route
                LEFT JOIN planet_osm_line w ON route.edge = w.gid
            )
            SELECT row_to_json(fc)
            FROM (
                SELECT 'FeatureCollection' AS type, array_to_json(array_agg(f)) AS features
                FROM (
                    SELECT 
                        'Feature' AS type,
                        ST_AsGeoJSON(ST_Transform(ST_Collect(ksp.way), 4326))::json AS geometry,
                        json_build_object('path_id', ksp.path_seq, 'total_cost', SUM(ksp.cost)) AS properties
                    FROM ksp
                    GROUP BY ksp.path_seq
                ) AS f
            ) AS fc;
        """)

        with engine.connect() as connection:
            start_time = time.time()
            result = connection.execute(sql_query).fetchone()
            end_time = time.time()
            compute_time = (end_time - start_time) * 1000

            if result and result[0]:
                geojson_data = result[0]
                # --- CORRECCIÓN DEL BUG ---
                # Siempre añade las 'properties' al GeoJSON, incluso si no se encuentran 'features'
                geojson_data['properties'] = {'compute_time_ms': compute_time}
                return geojson_data, 200
            else:
                return jsonify({"error": "No se encontraron k rutas alternativas."}), 404

    except Exception as e:
        print(f"Error en el cálculo de ruta kSP: {e}")
        return jsonify({"error": str(e)}), 500

# --- RUTAS PARA SERVIR EL SITIO WEB ESTÁTICO (Leaflet) ---
@app.route('/')
def root():
    return send_from_directory('SitioWeb', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('SitioWeb', path)

# --- INICIAR EL SERVIDOR ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
