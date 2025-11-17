import requests
import os

# URL del extracto completo de Chile desde Geofabrik
url = "http://download.geofabrik.de/south-america/chile-latest.osm.pbf"

# Nombre del archivo de salida
output_filename = "Infraestructura/region_data.osm.pbf"

print(f"Descargando datos desde: {url}")

try:
    # Realizar la petición GET para descargar el archivo
    response = requests.get(url, stream=True)
    response.raise_for_status() # Lanza un error si la descarga falla

    # Escribir el contenido en el archivo de salida
    with open(output_filename, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    print(f"Datos guardados exitosamente en: {output_filename}")

except requests.exceptions.RequestException as e:
    print(f"Error al descargar el archivo: {e}")
