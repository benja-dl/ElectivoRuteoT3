import time
from sqlalchemy import create_engine, text

# --- CONFIGURACIÓN DE LA BASE DE DATOS ---
DB_NAME = "tourdata_db"
DB_USER = "postgres"
DB_PASS = "tu_contraseña_segura" # ¡CAMBIA ESTO!
DB_HOST = "db"
DB_PORT = "5432"

db_url = f'postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
engine = create_engine(db_url)

print("Iniciando el proceso de modelado de costos (VERSIÓN FINAL Y ROBUSTA)...")

# Usamos una transacción explícita para asegurar que todo se guarde
with engine.connect() as connection:
    trans = connection.begin()
    try:
        # --- 1. PREPARACIÓN ---
        print("Preparando columnas 'prob_falla' y 'cost_resiliente'...")
        connection.execute(text("ALTER TABLE planet_osm_line ADD COLUMN IF NOT EXISTS prob_falla REAL DEFAULT 0.0;"))
        connection.execute(text("ALTER TABLE planet_osm_line ADD COLUMN IF NOT EXISTS cost_resiliente REAL DEFAULT 0.0;"))

        print("Reiniciando todos los costos y probabilidades (excluyendo ferries)...")
        connection.execute(text("""
            UPDATE planet_osm_line 
            SET prob_falla = 0.0, 
                cost_resiliente = CASE 
                                    WHEN highway = 'ferry' THEN 999999999 
                                    ELSE ST_Length(way) 
                                  END;
        """))

        # --- 2. PENALIZACIÓN POR WAZE ---
        print("Modelando penalización (Waze)...")
        sql_waze = text("""
            UPDATE planet_osm_line
            SET prob_falla = LEAST(1.0, prob_falla + 0.75)
            WHERE gid IN (
                SELECT DISTINCT c.gid
                FROM planet_osm_line AS c, amenazas_waze AS a
                WHERE ST_DWithin(c.way, ST_Transform(a.geom, 3857), 300) 
                AND c.highway != 'ferry'
                AND a.tipo_alerta IN ('JAM', 'ACCIDENT', 'ROAD_CLOSED')
            )
        """)
        result = connection.execute(sql_waze)
        print(f"{result.rowcount} calles afectadas por Waze.")

        # --- 3. PENALIZACIÓN POR ANTENAS SATURADAS ---
        print("Modelando penalización (Antenas Saturadas)...")
        sql_saturadas = text("""
            UPDATE planet_osm_line
            SET prob_falla = LEAST(1.0, prob_falla + 0.50),
                cost_resiliente = cost_resiliente * 100 
            WHERE gid IN (
                SELECT DISTINCT c.gid 
                FROM planet_osm_line AS c, antenas_saturadas AS a
                WHERE ST_DWithin(c.way, ST_Transform(a.geom, 3857), 300) 
                AND c.highway != 'ferry'
            )
        """)
        result = connection.execute(sql_saturadas)
        print(f"{result.rowcount} calles afectadas por antenas saturadas.")

        # --- 4. CÁLCULO DE COSTO FINAL RESILIENTE ---
        print("Ajustando costos resilientes por probabilidad de falla acumulada...")
        connection.execute(text("""
            UPDATE planet_osm_line 
            SET cost_resiliente = cost_resiliente * (1 + prob_falla) 
            WHERE highway != 'ferry';
        """))

        # --- 5. BONIFICACIÓN POR ANTENAS BUENAS ---
        print("Aplicando bonificación (Antenas Buenas)...")
        sql_buenas = text("""
        UPDATE planet_osm_line AS calles
        SET cost_resiliente = cost_resiliente * 0.1
        WHERE 
            calles.prob_falla = 0.0
            AND calles.highway != 'ferry'
            AND EXISTS (
                SELECT 1 FROM antenas
                WHERE ST_DWithin(calles.way, ST_Transform(antenas.geom, 3857), 750)
                AND antenas.tecnologia IN ('4G', '5G', '3G/5G', '4G/5G')
            );
        """)
        result = connection.execute(sql_buenas)
        print(f"{result.rowcount} calles bonificadas por buena cobertura.")

        trans.commit()
        print("¡Modelado de costos resilientes (FINAL) completado y guardado!")

    except Exception as e:
        print(f"ERROR DURANTE EL MODELADO DE COSTOS: {e}")
        trans.rollback()
        print("¡Cambios revertidos debido a un error!")
