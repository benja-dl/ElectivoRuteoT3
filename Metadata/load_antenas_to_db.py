import json
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡CAMBIA ESTO!
DB_HOST = "db"
DB_PORT = "5432"

input_json_path = 'Metadata/antenas.json'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

try:
    with open(input_json_path, 'r') as f:
        data = json.load(f)

    with engine.connect() as connection:
        print("Limpiando datos antiguos de la tabla 'antenas'...")
        connection.execute(text("TRUNCATE TABLE antenas RESTART IDENTITY;"))

        print(f"Cargando {len(data)} registros de antenas en la base de datos...")
        for antena in data:
            lon = antena["coordenadas"]["lon"]
            lat = antena["coordenadas"]["lat"]
            # Usamos ST_MakePoint para crear un punto geoespacial a partir de las coordenadas
            sql = text(f"""
                INSERT INTO antenas (operador, tecnologia, geom)
                VALUES ('{antena["operador"]}', '{antena["tecnologia"]}', ST_SetSRID(ST_MakePoint({lon}, {lat}), 4326));
            """)
            connection.execute(sql)

        connection.commit()
    print("Carga de metadatos de antenas completada.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo de entrada '{input_json_path}'")
except Exception as e:
    print(f"Ocurrió un error durante la carga a la base de datos: {e}")
