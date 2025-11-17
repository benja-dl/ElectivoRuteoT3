// --- 1. Inicialización del Mapa ---
const map = L.map('map').setView([-53.16, -70.91], 10); // Centrado en Magallanes
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
}).addTo(map);

// --- 2. Variables para Almacenar las Capas ---
let routeLayer = L.layerGroup().addTo(map);
let resilientRouteLayer = L.layerGroup().addTo(map);
let contingencyRouteLayer = L.layerGroup().addTo(map);
let kspRouteLayer = L.layerGroup().addTo(map); // Capa para k-Shortest Path
let cplexRouteLayer = L.layerGroup().addTo(map); // Capa para CPLEX (Placeholder)
let antennaLayer = L.layerGroup().addTo(map);
let saturatedAntennaLayer = L.layerGroup().addTo(map);
let threatLayer = L.layerGroup().addTo(map);
let failureLayer = L.layerGroup().addTo(map);

// --- 3. Cargar Datos y Rellenar Capas ---
fetch('ruta_ejemplo.geojson').then(r => r.json()).then(data => { L.geoJSON(data, { style: { color: "#e60000", weight: 5, opacity: 0.8 } }).addTo(routeLayer); });
fetch('antenas.geojson').then(r => r.json()).then(data => { L.geoJSON(data, { onEachFeature: (f, l) => { l.bindPopup(`<strong>ANTENA</strong><br>${f.properties.Empresa}<br>${f.properties["Nombre Comercial Tecnología"]}`); } }).addTo(antennaLayer); });
fetch('antenas_saturadas.geojson').then(r => r.json()).then(data => { L.geoJSON(data, { pointToLayer: (f, l) => L.marker(l, { icon: L.icon({ iconUrl: 'https://cdn-icons-png.flaticon.com/128/1828/1828843.png', iconSize: [25, 25] }) }), onEachFeature: (f, l) => { l.bindPopup(`<strong>ANTENA SATURADA</strong><br>${f.properties.Empresa}<br>${f.properties.Dirección}`); } }).addTo(saturatedAntennaLayer); });
fetch('weather_threats.geojson').then(r => r.json()).then(data => { L.geoJSON(data, { pointToLayer: (f, l) => { const i = f.properties.icono; return L.marker(l, { icon: L.icon({ iconUrl: `https://openweathermap.org/img/wn/${i}@2x.png`, iconSize: [50, 50], shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png', shadowSize: [41, 41], shadowAnchor: [12, 41] }) }); }, onEachFeature: (f, l) => { l.bindPopup(`<strong>Clima en ${f.properties.region}</strong><br>${f.properties.descripcion}`); } }).addTo(threatLayer); });

// --- 4. Lógica del Panel de Control de Capas ---
document.getElementById('check-ruta').addEventListener('change', (e) => e.target.checked ? map.addLayer(routeLayer) : map.removeLayer(routeLayer));
document.getElementById('check-ruta-resiliente').addEventListener('change', (e) => e.target.checked ? map.addLayer(resilientRouteLayer) : map.removeLayer(resilientRouteLayer));
document.getElementById('check-ruta-contingencia').addEventListener('change', (e) => e.target.checked ? map.addLayer(contingencyRouteLayer) : map.removeLayer(contingencyRouteLayer));
document.getElementById('check-ruta-ksp').addEventListener('change', (e) => e.target.checked ? map.addLayer(kspRouteLayer) : map.removeLayer(kspRouteLayer));
document.getElementById('check-ruta-cplex').addEventListener('change', (e) => e.target.checked ? map.addLayer(cplexRouteLayer) : map.removeLayer(cplexRouteLayer));
document.getElementById('check-antenas').addEventListener('change', (e) => e.target.checked ? map.addLayer(antennaLayer) : map.removeLayer(antennaLayer));
document.getElementById('check-antenas-saturadas').addEventListener('change', (e) => e.target.checked ? map.addLayer(saturatedAntennaLayer) : map.removeLayer(saturatedAntennaLayer));
document.getElementById('check-amenazas').addEventListener('change', (e) => e.target.checked ? map.addLayer(threatLayer) : map.removeLayer(threatLayer));

// --- CORRECCIÓN DEL ERROR DE TIPEO ---
document.getElementById('check-fallas').addEventListener('change', (e) => e.target.checked ? map.addLayer(failureLayer) : map.removeLayer(failureLayer));
// ------------------------------------

// --- 5. Lógica de Ruteo ---
const startInput = document.getElementById('start-point');
const geolocateBtn = document.getElementById('geolocate-btn');
const calculateBtn = document.getElementById('calculate-route-btn');
const contingencyBtn = document.getElementById('contingency-route-btn');
let userLocationMarker = null;

function onLocationFound(e) {
    const latlng = e.latlng;
    startInput.value = `${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`;
    if (userLocationMarker) map.removeLayer(userLocationMarker);
    userLocationMarker = L.marker(latlng).addTo(map).bindPopup("¡Estás aquí!").openPopup();
    map.setView(latlng, 13);
}
function onLocationError(e) { alert("No se pudo obtener la geolocalización."); }

map.on('locationfound', onLocationFound);
map.on('locationerror', onLocationError);
map.locate({ setView: true, maxZoom: 16 });
geolocateBtn.addEventListener('click', () => map.locate({ setView: true, maxZoom: 16 }));

function getRouteParams() {
    const startCoords = startInput.value.split(',');
    const endCoords = document.getElementById('end-point').value.split(',');
    if (startCoords.length < 2 || endCoords.length < 2) {
        alert("Por favor, ingresa coordenadas válidas (ej: -33.45, -70.66)");
        return null;
    }
    return {
        start: { lat: parseFloat(startCoords[0]), lon: parseFloat(startCoords[1]) },
        end: { lat: parseFloat(endCoords[0]), lon: parseFloat(endCoords[1]) }
    };
}

// Botón "Calcular Ruta (Normal)" - Calcula Roja, Verde, kSP y CPLEX (Placeholder)
calculateBtn.addEventListener('click', () => {
    const routeRequest = getRouteParams();
    if (!routeRequest) return;

    routeLayer.clearLayers();
    resilientRouteLayer.clearLayers();
    contingencyRouteLayer.clearLayers();
    kspRouteLayer.clearLayers();
    cplexRouteLayer.clearLayers();
    failureLayer.clearLayers();
    console.log("Calculando todas las rutas...", routeRequest);
    
    // 1. Ruta Peor Caso (Roja)
    fetch('/api/calculate_route', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(routeRequest) })
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            const time = data.properties.compute_time_ms.toFixed(2);
            L.geoJSON(data, { style: { color: "#e60000", weight: 5, opacity: 0.8 } }).addTo(routeLayer).bindPopup(`<b>Ruta Peor Caso</b><br>Tiempo: ${time} ms`).openPopup();
        }).catch(e => alert("No se pudo calcular la ruta (Peor Caso)."));

    // 2. Ruta Resiliente (Verde)
    fetch('/api/calculate_resilient_route', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(routeRequest) })
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            const time = data.properties.compute_time_ms.toFixed(2);
            L.geoJSON(data, { style: { color: "#00b300", weight: 5, opacity: 0.8, dashArray: '10, 5' } }).addTo(resilientRouteLayer).bindPopup(`<b>Ruta Resiliente</b><br>Tiempo: ${time} ms`).openPopup();
        }).catch(e => alert("No se pudo calcular la ruta (Resiliente)."));
        
    // 3. k-Shortest Path (kSP) (NUEVO)
    fetch('/api/calculate_ksp_route', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(routeRequest) })
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            
            const time = data.properties.compute_time_ms.toFixed(2);
            console.log(`Rutas kSP recibidas en ${time} ms`);
            
            // --- CORRECCIÓN DEL BUG: Comprobar si hay features ---
            if (data.features && data.features.length > 0) {
                const styles = [
                    { color: '#6a0dad', weight: 4, opacity: 0.7, dashArray: '5, 5' },
                    { color: '#800080', weight: 4, opacity: 0.7, dashArray: '5, 5' },
                    { color: '#9932CC', weight: 4, opacity: 0.7, dashArray: '5, 5' }
                ];
                
                data.features.forEach((route, index) => {
                    L.geoJSON(route, { style: styles[index % styles.length] })
                     .addTo(kspRouteLayer)
                     .bindPopup(`<b>Ruta kSP #${index + 1}</b><br>Costo: ${route.properties.total_cost.toFixed(0)}<br>Tiempo Total (kSP): ${time} ms`);
                });
            } else {
                console.log("kSP no devolvió rutas alternativas.");
            }
            // ----------------------------------------------------

        }).catch(e => {
            console.error('Error al calcular las rutas kSP:', e);
            alert("No se pudo calcular las rutas kSP.");
        });

    // 4. CPLEX/Gurobi (Placeholder) (NUEVO)
    fetch('/api/calculate_resilient_route', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(routeRequest) })
        .then(r => r.json()).then(data => {
            if (data.error) throw new Error(data.error);
            L.geoJSON(data, { style: { color: "#FFA500", weight: 3, opacity: 1, dashArray: '2, 8' } }) // Naranja
             .addTo(cplexRouteLayer)
             .bindPopup(`<b>Ruta CPLEX (Simulada)</b><br>Esta es una simulación.<br>Tiempo: N/A`);
        }).catch(e => console.error("Error al simular ruta CPLEX:", e));
});

// Botón "Calcular Ruta (Contingencia)" - Calcula Fucsia y Azul
contingencyBtn.addEventListener('click', () => {
    const routeRequest = getRouteParams();
    if (!routeRequest) return;

    console.log("Iniciando cálculo de contingencia...");
    
    // Limpiamos capas de contingencia y fallas
    contingencyRouteLayer.clearLayers();
    failureLayer.clearLayers();
    // Mantenemos las rutas Roja y Verde para comparar
    
    // 1. Simulamos las fallas
    fetch('/api/simulate_failures')
        .then(response => response.json())
        .then(failData => {
            console.log("Fallas simuladas recibidas:", failData);
            
            // 2. Dibujamos las fallas en el mapa (líneas fucsias)
            L.geoJSON(failData, {
                style: { color: "#FF00FF", weight: 8, opacity: 1.0 }
            }).addTo(failureLayer).bindPopup("¡ENLACE FALLIDO!");
            
            const failed_gids = failData.features.map(feature => feature.properties.gid);
            
            // 3. Preparamos la nueva solicitud de ruta, AÑADIENDO las fallas
            const contingencyRequest = {
                ...routeRequest,
                failed_gids: failed_gids
            };
            
            alert(`Simulación completada: ${failed_gids.length} enlaces fallaron. Calculando ruta de contingencia...`);
            
            // 4. Llamamos a la API de contingencia
            return fetch('/api/calculate_contingency_route', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(contingencyRequest)
            });
        })
        .then(response => response.json())
        .then(routeData => {
            if (routeData.error) throw new Error(routeData.error);
            
            // 5. Dibujamos la nueva ruta de contingencia (Azul)
            const time = routeData.properties.compute_time_ms.toFixed(2);
            L.geoJSON(routeData, { 
                style: { color: "#0000FF", weight: 4, opacity: 1.0, dashArray: '2, 6' }
            }).addTo(contingencyRouteLayer).bindPopup(`<b>Ruta de Contingencia</b><br>Tiempo: ${time} ms`).openPopup();
        })
        .catch(error => {
            console.error('Error al calcular la ruta de contingencia:', error);
            alert(`No se pudo calcular la ruta de contingencia: ${error.message}`);
        });
});
