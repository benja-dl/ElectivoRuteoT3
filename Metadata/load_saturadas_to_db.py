import json
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡CAMBIA ESTO!
DB_HOST = "db"
DB_PORT = "5432"

INPUT_JSON_PATH = 'SitioWeb/antenas_saturadas.geojson'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

try:
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with engine.connect() as connection:
        print("Limpiando datos antiguos de la tabla 'antenas_saturadas'...")
        connection.execute(text("TRUNCATE TABLE antenas_saturadas RESTART IDENTITY;"))

        print(f"Cargando {len(data['features'])} antenas saturadas en la base de datos...")

        for feature in data['features']:
            props = feature['properties']
            lon = feature['geometry']['coordinates'][0]
            lat = feature['geometry']['coordinates'][1]

            sql = text(f"""
                INSERT INTO antenas_saturadas (id_antena, operador, comuna, geom)
                VALUES (:id, :operador, :comuna, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326));
            """)

            connection.execute(sql, {
                "id": props.get('ID'),
                "operador": props.get('Empresa'),
                "comuna": props.get('Comuna'),
                "lon": lon,
                "lat": lat
            })

        connection.commit()
    print("Carga de antenas saturadas completada.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo de entrada '{INPUT_JSON_PATH}'")
except Exception as e:
    print(f"Ocurrió un error durante la carga a la base de datos: {e}")
