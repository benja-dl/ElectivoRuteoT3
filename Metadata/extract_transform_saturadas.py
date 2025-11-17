import csv
import json
import os

INPUT_CSV = 'Metadata/Infraestructura_Saturada.csv'
OUTPUT_GEOJSON = 'SitioWeb/antenas_saturadas.geojson'

geojson_output = {
    "type": "FeatureCollection",
    "features": []
}

print(f"Iniciando transformación de {INPUT_CSV}...")

try:
    # Usamos 'latin-1' para los caracteres especiales de SUBTEL
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as infile:
        reader = csv.DictReader(infile, delimiter=';')

        count = 0
        for row in reader:
            try:
                # Corrección: reemplazar coma por punto y convertir a float
                lat_str = row.get('Latitud').replace(',', '.')
                lon_str = row.get('Longitud').replace(',', '.')

                lat = float(lat_str)
                lon = float(lon_str)

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": row # Copiamos toda la info del CSV
                }
                geojson_output["features"].append(feature)
                count += 1
            except Exception as e:
                print(f"Error procesando fila: {row}. Error: {e}")

    print(f"Se procesaron y convirtieron {count} antenas saturadas.")

    with open(OUTPUT_GEOJSON, 'w', encoding='utf-8') as outfile:
        json.dump(geojson_output, outfile, indent=4)

    print(f"Transformación completada. Archivo guardado en: {OUTPUT_GEOJSON}")

except FileNotFoundError:
    print(f"Error: No se encontró el archivo de entrada '{INPUT_CSV}'")
except Exception as e:
    print(f"Ocurrió un error inesperado: {e}")
