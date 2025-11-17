import csv
import json
import re
import os

INPUT_CSV = 'Metadata/Antenas_en_Servicio_Magallanes.csv'
OUTPUT_GEOJSON = 'SitioWeb/antenas.geojson'

def dms_to_decimal(dms_str):
    """
    Versión robusta que extrae números de la cadena, ignorando
    símbolos de grado, comillas o caracteres de codificación corruptos.
    """
    try:
        parts = re.findall(r"[\d\.]+", dms_str)
        if len(parts) < 3:
            print(f"Error de parseo: No se encontraron 3 números en '{dms_str}'")
            return None

        degrees = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])

        decimal = degrees + (minutes / 60) + (seconds / 3600)
        return -abs(decimal) # Asumir Sur y Oeste (negativo)

    except Exception as e:
        print(f"Error al convertir DMS: '{dms_str}' | Partes encontradas: {parts} | Error: {e}")
        return None

geojson_output = {
    "type": "FeatureCollection",
    "features": []
}

print(f"Iniciando transformación de {INPUT_CSV}...")

try:
    #
    # --- ESTA ES LA LÍNEA DE LA SOLUCIÓN (Python) ---
    # Usamos 'utf-8-sig' para leer UTF-8 y omitir el BOM (caracteres ï»¿)
    #
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile, delimiter=';')

        count = 0
        for row in reader:
            lat = dms_to_decimal(row.get('Latitud'))
            lon = dms_to_decimal(row.get('Longitud'))

            if lat is not None and lon is not None:
                # Limpiamos las propiedades para el popup
                properties = row.copy()
                properties['Latitud_Decimal'] = lat
                properties['Longitud_Decimal'] = lon

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": properties
                }
                geojson_output["features"].append(feature)
                count += 1

    print(f"Se procesaron y convirtieron {count} antenas.")

    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as outfile:
        json.dump(geojson_output, outfile, indent=4)

    print(f"Transformación completada. Archivo guardado en: {OUTPUT_GEOJSON}")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo de entrada '{INPUT_CSV}'")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
