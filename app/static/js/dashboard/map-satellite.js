// dashboard/map-satellite.js — nubes reales (satelite NASA GOES-East)
// GeoColor: foto normal, buena para vistazo rapido.
// Band13 infrarrojo: temperatura de la punta de la nube (mas fria = mas
// alta = mas probable que sea tormenta), util para juzgar severidad.

const CAPAS_SATELITE = {
  geocolor: { layer: 'GOES-East_ABI_GeoColor', tileMatrixSet: 'GoogleMapsCompatible_Level7', maxZoom: 7 },
  infrared: { layer: 'GOES-East_ABI_Band13_Clean_Infrared', tileMatrixSet: 'GoogleMapsCompatible_Level6', maxZoom: 6 },
};
let satLayer = null;
let satMaxZoom = 7;

// Pasado el zoom real del satelite no hay tiles mas finos. Hasta
// OVERZOOM_TOPE_ZOOM se arma un mosaico con los tiles del ultimo nivel real,
// cada uno como MapImage georreferenciada: ArcGIS los mueve con el mapa y
// cubren toda la vista, en vez de una sola imagen que se cortaba en el borde.
const OVERZOOM_TOPE_ZOOM = 11;
const MERC_MAX = Math.PI * 6378137;

function tilesQueCubren(ext, z, margen = 1) {
  const n = Math.pow(2, z);
  const tam = (2 * MERC_MAX) / n;
  const limitar = v => Math.min(n - 1, Math.max(0, v));
  const c0 = limitar(Math.floor((ext.xmin + MERC_MAX) / tam) - margen);
  const c1 = limitar(Math.floor((ext.xmax + MERC_MAX) / tam) + margen);
  const r0 = limitar(Math.floor((MERC_MAX - ext.ymax) / tam) - margen);
  const r1 = limitar(Math.floor((MERC_MAX - ext.ymin) / tam) + margen);
  const tiles = [];
  for (let row = r0; row <= r1; row++) {
    for (let col = c0; col <= c1; col++) {
      const xmin = -MERC_MAX + col * tam;
      const ymax = MERC_MAX - row * tam;
      tiles.push({ row, col, extent: { xmin, ymin: ymax - tam, xmax: xmin + tam, ymax } });
    }
  }
  return tiles;
}

let satMosaico = null;
let satMapImage = null;
let satUrlTile = null;
let satTilesPuestos = new Set();

function completarMosaico() {
  if (!satMosaico || !satMapImage || !satUrlTile || !rainMap || !rainMap.extent) return;
  for (const t of tilesQueCubren(rainMap.extent, satMaxZoom)) {
    const clave = `${t.row}/${t.col}`;
    if (satTilesPuestos.has(clave)) continue;
    satTilesPuestos.add(clave);
    satMosaico.addImage(new satMapImage({
      extent: Object.assign({ spatialReference: { wkid: 102100 } }, t.extent),
      href: satUrlTile(satMaxZoom, t.row, t.col),
    }));
  }
}

// Tiles de referencia (oeste/centro/este) para probar si un horario tiene
// datos reales en toda la vista, no solo en un punto — GOES a veces hace
// escaneos parciales que no cubren todo el continente a la vez.
const TILES_REGION = {
  GoogleMapsCompatible_Level6: [
    { level: 6, row: 30, col: 16 }, { level: 6, row: 30, col: 18 }, { level: 6, row: 30, col: 21 },
  ],
  GoogleMapsCompatible_Level7: [
    { level: 7, row: 61, col: 33 }, { level: 7, row: 61, col: 37 }, { level: 7, row: 61, col: 42 },
  ],
};

function horasGibsCandidatas() {
  // GIBS publica en pasos de 10 min pero con retraso variable de
  // procesamiento; probamos varios horarios recientes y usamos el primero
  // que si tenga imagen real para nosotros.
  const candidatos = [];
  for (let atras = 20; atras <= 80; atras += 10) {
    const t = new Date(Date.now() - atras * 60 * 1000);
    t.setUTCSeconds(0, 0);
    t.setUTCMinutes(Math.floor(t.getUTCMinutes() / 10) * 10);
    candidatos.push(t.toISOString().replace(/\.\d+Z$/, 'Z'));
  }
  return candidatos;
}

async function tileTieneDatos(cfg, tile, tiempo) {
  const url = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${tiempo}/${cfg.tileMatrixSet}/${tile.level}/${tile.row}/${tile.col}.png`;
  try {
    const res = await fetch(url);
    if (!res.ok) return false;
    const blob = await res.blob();
    // GIBS a veces responde 200 con una imagen "vacia" (transparente, muy
    // chica) cuando no hay datos reales para ese tile puntual.
    return blob.size > 2000;
  } catch (e) {
    return false;
  }
}

async function probarHorario(cfg, tiles, tiempo) {
  // Exige que TODOS los puntos de referencia tengan datos, no solo uno.
  const resultados = await Promise.all(tiles.map(tile => tileTieneDatos(cfg, tile, tiempo)));
  return resultados.every(ok => ok) ? tiempo : null;
}

async function encontrarHoraValida(cfg) {
  const tiles = TILES_REGION[cfg.tileMatrixSet];
  const candidatos = horasGibsCandidatas();
  const resultados = await Promise.all(candidatos.map(t => probarHorario(cfg, tiles, t)));
  return resultados.find(t => t !== null) || null;
}

function actualizarVisibilidadSatelite() {
  if (!rainMap) return;
  const zoom = rainMap.getZoom();
  if (satLayer) satLayer.setVisibility(zoom <= satMaxZoom);
  if (satMosaico) {
    const mostrarMosaico = zoom > satMaxZoom && zoom <= OVERZOOM_TOPE_ZOOM;
    satMosaico.setVisibility(mostrarMosaico);
    if (mostrarMosaico) completarMosaico();
  }
}

let satRetryTimer = null;
let satSinDatosSeguidos = 0;
const SAT_REINTENTO_MS = 90 * 1000;
const SAT_REINTENTOS_MAX = 3;

function capaSatelitePorDefectoSegunHora() {
  // De madrugada/noche GeoColor sale oscuro (render nocturno con luces de
  // ciudad); el infrarrojo muestra nubes util 24/7, asi que se deja por
  // defecto fuera del horario diurno de la region (Colombia = UTC-5).
  const sel = document.getElementById('gwSatSelect');
  if (!sel) return;
  const horaCol = (new Date().getUTCHours() + 19) % 24;
  sel.value = (horaCol >= 7 && horaCol < 18) ? 'geocolor' : 'infrared';
}

async function loadSatelliteLayer() {
  if (!esriMods || !rainMap) return;
  if (satRetryTimer) { clearTimeout(satRetryTimer); satRetryTimer = null; }
  const select = document.getElementById('gwSatSelect');
  const clave = select ? select.value : 'geocolor';
  const cfg = CAPAS_SATELITE[clave] || CAPAS_SATELITE.geocolor;
  satMaxZoom = cfg.maxZoom;

  const tiempo = await encontrarHoraValida(cfg);
  if (!tiempo) {
    console.warn('Sin horario valido de satelite NASA para esta zona ahora mismo');
    // GIBS a veces todavia esta procesando el horario mas reciente cuando
    // lo probamos; reintenta pronto en vez de esperar los 10 min normales.
    if (satSinDatosSeguidos < SAT_REINTENTOS_MAX) {
      satSinDatosSeguidos++;
      satRetryTimer = setTimeout(loadSatelliteLayer, SAT_REINTENTO_MS);
    }
    return;
  }
  satSinDatosSeguidos = 0;

  const horaEl = document.getElementById('gwSatHora');
  if (horaEl) {
    horaEl.textContent = 'Imagen: ' + new Date(tiempo).toLocaleTimeString(
      'es-CO', { hour: '2-digit', minute: '2-digit' });
  }

  const base = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${tiempo}/${cfg.tileMatrixSet}`;
  const tileUrl = `${base}/\${level}/\${row}/\${col}.png`;
  const urlTile = (z, row, col) => `${base}/${z}/${row}/${col}.png`;

  function ponerCapa() {
    require(["esri/layers/WebTiledLayer", "esri/layers/MapImageLayer", "esri/layers/MapImage"],
      function (WebTiledLayer, MapImageLayer, MapImage) {
        if (!rainMap) return;
        if (satLayer) rainMap.removeLayer(satLayer);
        if (satMosaico) rainMap.removeLayer(satMosaico);
        satLayer = new WebTiledLayer(tileUrl, { id: "satelite", opacity: 0.7 });
        satMosaico = new MapImageLayer({ id: "satelite-mosaico", opacity: 0.7 });
        satMapImage = MapImage;
        satUrlTile = urlTile;
        satTilesPuestos = new Set();
        rainMap.addLayer(satLayer);
        rainMap.addLayer(satMosaico);
        actualizarVisibilidadSatelite();
      });
  }

  ponerCapa();
  // Segunda pasada unos segundos despues: los tiles que ya cargaron salen
  // de la cache al instante, y los que fallaron por congestion de
  // conexiones simultaneas en la carga inicial se vuelven a pedir.
  satRetryTimer = setTimeout(() => { satRetryTimer = null; ponerCapa(); }, 4000);
}
