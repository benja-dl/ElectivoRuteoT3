import json
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡CAMBIA ESTO!
DB_HOST = "db"
DB_PORT = "5432"

INPUT_JSON_PATH = 'Amenazas/waze_alerts.json'

engine = create_engine(f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}')

try:
    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with engine.connect() as connection:
        print("Limpiando datos antiguos de la tabla 'amenazas_waze'...")
        connection.execute(text("TRUNCATE TABLE amenazas_waze RESTART IDENTITY;"))

        print(f"Cargando {len(data)} alertas de Waze en la base de datos...")

        alerts_loaded = 0
        for alerta in data:
            if not (alerta.get("coordenadas") and alerta["coordenadas"].get("lon") and alerta["coordenadas"].get("lat")):
                continue

            lon = alerta["coordenadas"]["lon"]
            lat = alerta["coordenadas"]["lat"]

            # Query SQL corregida
            sql = text(f"""
                INSERT INTO amenazas_waze (waze_id, tipo_alerta, subtipo_alerta, descripcion, geom)
                VALUES (:waze_id, :tipo, :subtipo, :desc, ST_SetSRID(ST_MakePoint(:lon, :lat), 4326))
                ON CONFLICT (waze_id) DO NOTHING;
            """)

            connection.execute(sql, {
                "waze_id": alerta.get("id"),
                "tipo": alerta.get("tipo_alerta"),
                "subtipo": alerta.get("subtipo_alerta"),
                "desc": alerta.get("descripcion"),
                "lon": lon,
                "lat": lat
            })
            alerts_loaded += 1

        connection.commit()
    print(f"Carga de {alerts_loaded} amenazas de Waze completada.")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo de entrada '{INPUT_JSON_PATH}'")
except Exception as e:
    print(f"Ocurrió un error durante la carga a la base de datos: {e}")
