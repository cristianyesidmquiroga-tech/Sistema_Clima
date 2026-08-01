// dashboard/map-rain.js — mapa base, limites de municipios, estaciones y modal

const RAIN_COLORS = {
  sin_dato:   '#888888',
  sin_lluvia: '#bdbdbd',
  bajo:       '#4fc3f7',
  moderado:   '#66bb6a',
  alto:       '#ffa726',
  muy_alto:   '#e53935',
};

// Mapa hecho con ArcGIS API for JavaScript 3.28 (la misma libreria que usa
// SAB/IDIGER), con OpenStreetMapLayer como mapa base, para que se vea igual
// que la referencia. Es mas pesada que Leaflet a proposito.
let rainMap = null;
let esriMods = null;   // referencias a las clases de ArcGIS ya cargadas
let markersLayer = null;
let heatLayer = null;

// Techo de intensidad para el heatmap, en mm/h (tasa actual, no acumulado
// del dia). Interpolacion entre las 6 estaciones, no radar real.
const HEATMAP_RATE_MAX = 15;

function initRainMap() {
  const mapEl = document.getElementById('gwRainMap');
  if (!mapEl || typeof require === 'undefined') return;

  require([
    "esri/map", "esri/layers/OpenStreetMapLayer", "esri/layers/GraphicsLayer",
    "esri/layers/WebTiledLayer", "esri/graphic", "esri/geometry/Point",
    "esri/geometry/Polygon", "esri/SpatialReference", "esri/symbols/SimpleMarkerSymbol",
    "esri/symbols/SimpleLineSymbol", "esri/symbols/SimpleFillSymbol", "esri/renderers/HeatmapRenderer",
    "esri/InfoTemplate", "esri/Color", "dojo/domReady!"
  ], function (Map, OpenStreetMapLayer, GraphicsLayer, WebTiledLayer, Graphic,
               Point, Polygon, SpatialReference, SimpleMarkerSymbol, SimpleLineSymbol,
               SimpleFillSymbol, HeatmapRenderer, InfoTemplate, Color) {
    esriMods = { Graphic, Point, Polygon, SpatialReference, SimpleMarkerSymbol, SimpleLineSymbol, SimpleFillSymbol, HeatmapRenderer, InfoTemplate, Color, GraphicsLayer };

    rainMap = new Map("gwRainMap", {
      center: [-73.68, 5.96],  // ArcGIS usa [lon, lat], al reves que Leaflet
      zoom: 11,
      maxZoom: 12,
      logo: false,
    });
    rainMap.addLayer(new OpenStreetMapLayer());

    cargarLimitesMunicipios();

    markersLayer = new GraphicsLayer();
    markersLayer.setInfoTemplate(new InfoTemplate("${nombre}", "${lluviaTxt}<br>${tempTxt}<br><em>Click en el triángulo para ver el historial</em>"));
    markersLayer.on("click", function (evt) {
      const attrs = evt.graphic.attributes;
      if (attrs && attrs.stationId) openStationModal(attrs.stationId, attrs.nombre);
    });

    heatLayer = new GraphicsLayer();

    function alMapaListo() {
      rainMap.addLayer(heatLayer);
      rainMap.addLayer(markersLayer);
      // Un solo listener para toda la vida del mapa (zoom, pan y resize),
      // no registrado de nuevo en cada loadSatelliteLayer().
      rainMap.on("extent-change", actualizarVisibilidadSatelite);
      loadSatelliteLayer();
      fetchMapaLluvias();
    }
    if (rainMap.loaded) alMapaListo();
    else rainMap.on("load", alMapaListo);

    const satSelect = document.getElementById('gwSatSelect');
    if (satSelect) satSelect.addEventListener('change', loadSatelliteLayer);
  });
}

// ─── LIMITES DE MUNICIPIOS (Velez, Guavata, Barbosa, Puente Nacional) ──
// Datos de OpenStreetMap (Nominatim), guardados en /static/data/municipios_region.geojson.
function geojsonARings(geometry) {
  if (geometry.type === 'Polygon') return geometry.coordinates;
  if (geometry.type === 'MultiPolygon') return geometry.coordinates.reduce((acc, poly) => acc.concat(poly), []);
  return [];
}

async function cargarLimitesMunicipios() {
  if (!rainMap || !esriMods) return;
  try {
    const res = await fetch('/static/data/municipios_region.geojson');
    const geojson = await res.json();
    const { Graphic, Polygon, SpatialReference, SimpleFillSymbol, SimpleLineSymbol, Color, GraphicsLayer } = esriMods;
    const wgs84 = new SpatialReference({ wkid: 4326 });
    const borde = new SimpleLineSymbol(SimpleLineSymbol.STYLE_SOLID, new Color('#1c1e22'), 2);
    const simbolo = new SimpleFillSymbol(SimpleFillSymbol.STYLE_NULL, borde, null);

    const boundariesLayer = new GraphicsLayer();
    geojson.features.forEach(f => {
      const rings = geojsonARings(f.geometry);
      if (!rings.length) return;
      const poly = new Polygon({ rings, spatialReference: wgs84 });
      boundariesLayer.add(new Graphic(poly, simbolo));
    });
    // Se agrega justo arriba del basemap (indice 1) para quedar debajo de
    // los triangulos y el heatmap sin importar el orden de las promesas.
    rainMap.addLayer(boundariesLayer, 1);
  } catch (e) {
    console.error('Error cargando limites de municipios', e);
  }
}

function crearSimboloTriangulo(color) {
  const { SimpleMarkerSymbol, SimpleLineSymbol, Color } = esriMods;
  return new SimpleMarkerSymbol(
    SimpleMarkerSymbol.STYLE_TRIANGLE, 16,
    new SimpleLineSymbol(SimpleLineSymbol.STYLE_SOLID, new Color('#1c1e22'), 1.5),
    new Color(color)
  );
}

// ─── PARPADEO DE ESTACIONES CON LLUVIA ACTIVA AHORA MISMO ─────
let graficosParpadeando = [];
let parpadeoIniciado = false;
let parpadeoVisible = true;

function iniciarParpadeoEstaciones() {
  if (parpadeoIniciado) return;
  parpadeoIniciado = true;
  setInterval(() => {
    parpadeoVisible = !parpadeoVisible;
    graficosParpadeando.forEach(g => {
      if (parpadeoVisible) g.show(); else g.hide();
    });
  }, 550);
}

// Cuanto se mantiene parpadeando una estacion despues de que su tasa de
// lluvia vuelve a 0 (evita que el parpadeo se apague de golpe justo
// cuando el chubasco esta perdiendo intensidad).
const PARPADEO_COOLDOWN_MS = 10 * 60 * 1000;
const ultimaLluviaPorEstacion = new Map(); // stationId -> timestamp del ultimo lluvia_rate > 0

async function fetchMapaLluvias() {
  if (!rainMap || !markersLayer || !esriMods) return;
  try {
    const res = await fetch('/api/mapa_lluvias');
    const data = await res.json();

    const { Graphic, Point, SpatialReference, HeatmapRenderer } = esriMods;
    markersLayer.clear();
    heatLayer.clear();

    const wgs84 = new SpatialReference({ wkid: 4326 });
    const heatGraphics = [];
    const nuevosParpadeando = [];
    const ahora = Date.now();

    data.forEach(est => {
      if (est.lat == null || est.lon == null) return;
      const color = RAIN_COLORS[est.nivel] || RAIN_COLORS.sin_dato;
      const punto = new Point(est.lon, est.lat, wgs84);
      const rateTxt = est.lluvia_rate != null ? `${est.lluvia_rate.toFixed(1)} mm/h` : 'sin dato';
      const mmTxt = est.lluvia_mm != null ? `${est.lluvia_mm.toFixed(1)} mm` : 'sin dato';
      const tempTxt = est.temp != null ? `Temp: ${est.temp}°C` : '';
      const graphic = new Graphic(punto, crearSimboloTriangulo(color), {
        stationId: est.id, nombre: est.nombre, id: est.id,
        lluviaTxt: `Lluvia ahora: ${rateTxt}<br>Acumulado hoy: ${mmTxt}`, tempTxt: tempTxt,
      });
      markersLayer.add(graphic);

      if (est.lluvia_rate > 0) {
        ultimaLluviaPorEstacion.set(est.id, ahora);
        const intensidad = Math.min(est.lluvia_rate, HEATMAP_RATE_MAX);
        const gHeat = new Graphic(punto, null, { lluvia: intensidad });
        heatGraphics.push(gHeat);
      }

      // Parpadea si esta lloviendo ahora mismo, o si dejo de llover hace
      // menos de PARPADEO_COOLDOWN_MS.
      const ultimaVez = ultimaLluviaPorEstacion.get(est.id);
      if (est.lluvia_rate > 0 || (ultimaVez && ahora - ultimaVez < PARPADEO_COOLDOWN_MS)) {
        nuevosParpadeando.push(graphic);
      }
    });

    graficosParpadeando = nuevosParpadeando;
    iniciarParpadeoEstaciones();

    if (heatGraphics.length) {
      heatLayer.setRenderer(new HeatmapRenderer({
        field: 'lluvia', blurRadius: 25, maxPixelIntensity: HEATMAP_RATE_MAX, minPixelIntensity: 0,
      }));
      heatGraphics.forEach(g => heatLayer.add(g));
    }

    actualizarPromedioRegional(data);
  } catch (e) {
    console.error('Error cargando mapa de lluvias', e);
  }
}

function promedio(valores) {
  const validos = valores.filter(v => typeof v === 'number' && !isNaN(v));
  if (!validos.length) return null;
  return validos.reduce((a, b) => a + b, 0) / validos.length;
}

function actualizarPromedioRegional(data) {
  const elTemp = document.getElementById('gwRegionTemp');
  const elHum = document.getElementById('gwRegionHum');
  const elViento = document.getElementById('gwRegionViento');
  const elLluvia = document.getElementById('gwRegionLluvia');
  if (!elTemp) return;

  const tempProm = promedio(data.map(d => d.temp));
  const humProm = promedio(data.map(d => d.humedad));
  const vientoProm = promedio(data.map(d => d.viento));
  const lluviaProm = promedio(data.map(d => d.lluvia_mm));

  elTemp.textContent    = tempProm   != null ? `${tempProm.toFixed(1)}°C` : '--°C';
  elHum.textContent     = humProm    != null ? `${humProm.toFixed(0)}%`   : '--%';
  elViento.textContent  = vientoProm != null ? `${vientoProm.toFixed(1)} km/h` : '-- km/h';
  elLluvia.textContent  = lluviaProm != null ? `${lluviaProm.toFixed(1)} mm`   : '-- mm';
}

// ─── MODAL DE DETALLE POR ESTACION ────────────────────────────
let stationCharts = {};

function destruirStationCharts() {
  Object.values(stationCharts).forEach(c => c && c.destroy());
  stationCharts = {};
}

async function openStationModal(stationId, nombre) {
  if (!puedeClickear('modal-estacion-' + stationId)) return;
  const modal = document.getElementById('gwStationModal');
  const titulo = document.getElementById('gwStationModalTitle');
  if (!modal || !titulo) return;
  titulo.textContent = `${nombre} — últimas 24h`;
  modal.classList.add('show');

  try {
    const res = await fetch(`/api/estacion/${stationId}/historial?dias=1`);
    const data = await res.json();
    renderStationCharts(data);
  } catch (e) {
    console.error('Error cargando historial de estacion', e);
  }
}

function closeStationModal() {
  const modal = document.getElementById('gwStationModal');
  if (modal) modal.classList.remove('show');
}

function renderStationCharts(data) {
  destruirStationCharts();
  if (!data.length) return;

  // El modal siempre tiene fondo blanco (independiente del tema de la
  // pagina), asi que los textos de las graficas van siempre oscuros.
  const textColor = '#333333';
  const labels = data.map(d => {
    const t = new Date(d.timestamp);
    return t.getHours().toString().padStart(2, '0') + ':00';
  });

  const baseOpts = {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { labels: { color: textColor, font: { size: 10 }, boxWidth: 10 } } },
    scales: {
      x: { ticks: { color: textColor, font: { size: 9 } }, grid: { display: false } },
      y: { ticks: { color: textColor, font: { size: 9 } }, grid: { color: 'rgba(0,0,0,0.08)' } },
    },
  };

  stationCharts.temp = new Chart(document.getElementById('gwStChartTemp').getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Temp °C', data: data.map(d => d.temp_avg), borderColor: '#fbbc04', backgroundColor: 'rgba(251,188,4,0.08)', fill: true, tension: 0.4, pointRadius: 0, borderWidth: 2 },
      { label: 'Punto de Rocío °C', data: data.map(d => d.dewpt_avg), borderColor: '#66bb6a', backgroundColor: 'transparent', tension: 0.4, pointRadius: 0, borderWidth: 2 },
    ]},
    options: baseOpts,
  });

  stationCharts.wind = new Chart(document.getElementById('gwStChartWind').getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Viento km/h', data: data.map(d => d.viento_avg), borderColor: '#4fc3f7', backgroundColor: 'transparent', tension: 0.4, pointRadius: 0, borderWidth: 2 },
      { label: 'Ráfaga km/h', data: data.map(d => d.rafaga_max), borderColor: '#ffa726', backgroundColor: 'transparent', tension: 0.4, pointRadius: 0, borderWidth: 1.5, borderDash: [4, 3] },
    ]},
    options: baseOpts,
  });

  stationCharts.rain = new Chart(document.getElementById('gwStChartRain').getContext('2d'), {
    type: 'bar',
    data: { labels, datasets: [
      { label: 'Lluvia mm', data: data.map(d => d.lluvia_mm), backgroundColor: '#8ab4f8' },
    ]},
    options: baseOpts,
  });

  stationCharts.pressure = new Chart(document.getElementById('gwStChartPressure').getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Presión hPa (máx)', data: data.map(d => d.presion_max), borderColor: '#5c6bc0', backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, borderWidth: 2 },
    ]},
    options: baseOpts,
  });

  stationCharts.solar = new Chart(document.getElementById('gwStChartSolar').getContext('2d'), {
    type: 'line',
    data: { labels, datasets: [
      { label: 'Radiación Solar W/m²', data: data.map(d => d.radiacion_solar_max), borderColor: '#ff8a65', backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, borderWidth: 2, yAxisID: 'y' },
      { label: 'UV', data: data.map(d => d.uv_max), borderColor: '#ce93d8', backgroundColor: 'transparent', tension: 0.3, pointRadius: 0, borderWidth: 2, yAxisID: 'y1' },
    ]},
    options: { ...baseOpts, scales: { ...baseOpts.scales,
      y1: { position: 'right', ticks: { color: textColor, font: { size: 9 } }, grid: { display: false } } } },
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const closeBtn = document.getElementById('gwStationModalClose');
  if (closeBtn) closeBtn.addEventListener('click', closeStationModal);
  const modal = document.getElementById('gwStationModal');
  if (modal) modal.addEventListener('click', (e) => { if (e.target === modal) closeStationModal(); });
});
