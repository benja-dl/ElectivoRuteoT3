FROM python:3.11-slim

# Instala dependencias del sistema operativo (para Geopandas y osm2pgsql)
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gdal-bin \
    osm2pgsql \
    wget

WORKDIR /app

# Copia e instala las librerías de Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
