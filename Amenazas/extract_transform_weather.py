import requests
import json
import os

API_KEY = '177baa2c885d29d46865e249df1eb602'  # <-- ¡REEMPLAZA ESTO!
OUTPUT_JSON_PATH = 'SitioWeb/weather_threats.geojson' # Guardamos directo en SitioWeb

# Lista de ciudades clave (puedes añadir más)
ciudades = {
    "Arica": (-18.47, -70.32),
    "Santiago": (-33.45, -70.66),
    "Valparaiso": (-33.04, -71.61),
    "Punta Arenas": (-53.16, -70.91)
}

# Estructura base GeoJSON
geojson_output = {
    "type": "FeatureCollection",
    "features": []
}

print("Obteniendo datos climatológicos desde OpenWeatherMap...")

for ciudad, coords in ciudades.items():
    lat, lon = coords
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=es"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # --- TRANSFORMACIÓN a GeoJSON ---
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [data['coord']['lon'], data['coord']['lat']]
            },
            "properties": {
                "region": ciudad,
                "condicion_principal": data['weather'][0]['main'], # Ej: "Rain"
                "descripcion": data['weather'][0]['description'],
                "temperatura_celsius": data['main']['temp'],
                "viento_kmh": data['wind']['speed'] * 3.6, # m/s a km/h
                "icono": data['weather'][0]['icon'] # Código del ícono (ej: "10d")
            }
        }
        geojson_output["features"].append(feature)
        print(f"Datos de {ciudad} obtenidos con éxito.")

    except requests.exceptions.RequestException as e:
        print(f"Error al obtener datos para {ciudad}: {e}")

print(f"\nGuardando datos transformados en '{OUTPUT_JSON_PATH}'...")
with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as outfile:
    json.dump(geojson_output, outfile, indent=4)

print("Transformación de amenazas climatológicas completada.")
