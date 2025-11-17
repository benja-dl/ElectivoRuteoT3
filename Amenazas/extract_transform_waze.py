import WazeRouteCalculator
import json
import logging
import os

# --- CONFIGURACIÓN ---
# Definimos una ruta larga y representativa para capturar alertas
START_ADDRESS = 'Plaza de Armas, Santiago, Chile'
END_ADDRESS = 'Puente Alto, Chile'

OUTPUT_JSON_PATH = 'Amenazas/waze_alerts.json'

# Desactivamos los logs ruidosos de la librería
logging.basicConfig(level=logging.WARNING)

transformed_alerts = [] # Aquí guardaremos todas las alertas encontradas

try:
    print(f"Calculando ruta de Waze ({START_ADDRESS} -> {END_ADDRESS}) para obtener alertas en tiempo real...")

    # 1. Instanciamos la clase con las direcciones
    waze = WazeRouteCalculator.WazeRouteCalculator(START_ADDRESS, END_ADDRESS, region='EU')

    # 2. Calculamos las rutas. Esto devuelve un diccionario con los detalles.
    routes = waze.calc_all_routes_info()
    print(f"Se encontraron {len(routes)} rutas alternativas.")

    # --- TRANSFORMACIÓN ---
    # 3. Iteramos por cada ruta encontrada para extraer sus alertas
    for route_name, route_details in routes.items():

        # 3a. Extraer CONGESTIÓN (Jams)
        if 'jams' in route_details:
            for jam in route_details['jams']:
                transformed_alerts.append({
                    "id": jam.get('id'),
                    "tipo_alerta": "JAM", # Congestión
                    "subtipo_alerta": jam.get('type'), # Ej: "JAM_HEAVY_TRAFFIC"
                    "descripcion": jam.get('description'),
                    "coordenadas": {
                        "lat": jam.get('latitude'),
                        "lon": jam.get('longitude')
                    }
                })

        # 3b. Extraer OTRAS ALERTAS (Accidentes, Policía, etc.)
        if 'alerts' in route_details:
            for alert in route_details['alerts']:
                transformed_alerts.append({
                    "id": alert.get('id'),
                    "tipo_alerta": alert.get('type'), # Ej: "ACCIDENT", "POLICE", "ROAD_CLOSED"
                    "subtipo_alerta": alert.get('subtype'),
                    "descripcion": alert.get('description'),
                    "coordenadas": {
                        "lat": alert.get('latitude'),
                        "lon": alert.get('longitude')
                    }
                })

    # 4. Eliminar duplicados (ya que rutas alternativas pueden compartir alertas)
    unique_alerts = list({alert['id']: alert for alert in transformed_alerts}.values())

    print(f"Se encontraron {len(unique_alerts)} alertas únicas (congestión, choques, etc.).")
    print(f"Guardando datos transformados en '{OUTPUT_JSON_PATH}'...")

    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as outfile:
        json.dump(unique_alerts, outfile, indent=4)

    print("Transformación de amenazas de Waze completada.")

except WazeRouteCalculator.WRCError as e:
    print(f"Error específico de Waze: {e}")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
