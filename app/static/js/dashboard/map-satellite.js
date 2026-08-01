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

// Pasado el zoom real del satelite, la capa de tiles se esconde (no hay
// tiles reales mas alla). Ya se probo pedirle a WebTiledLayer tiles de
// niveles que no existen: repite la imagen completa en cada casillero
// (cuadricula duplicada, confuso). En su lugar, hasta OVERZOOM_TOPE_ZOOM
// se muestra una unica imagen estirada con CSS (satOverlayImg),
// reposicionada en cada zoom/pan con rainMap.toScreen(). El infrarrojo
// tiene menos zoom nativo que el GeoColor (maxZoom 6 vs 7), asi que se le
// da mas "extra" para que ambas capas lleguen al mismo tope final.
const OVERZOOM_TOPE_ZOOM = 11;
let satOverzoomTope = OVERZOOM_TOPE_ZOOM;
const REGION_CENTER = { lon: -73.68, lat: 5.96 };
const MERC_R = 6378137;
const MERC_MAX = Math.PI * MERC_R;

function tileDeLonLat(lon, lat, z) {
  const n = Math.pow(2, z);
  const col = Math.floor((lon + 180) / 360 * n);
  const latRad = lat * Math.PI / 180;
  const row = Math.floor((1 - Math.log(Math.tan(latRad) + 1 / Math.cos(latRad)) / Math.PI) / 2 * n);
  return { row, col };
}

function limitesTileMercator(row, col, z) {
  const tam = (2 * MERC_MAX) / Math.pow(2, z);
  const minX = -MERC_MAX + col * tam;
  const maxY = MERC_MAX - row * tam;
  return { minX, minY: maxY - tam, maxX: minX + tam, maxY };
}

let satOverlayImg = null;
let satOverlayBoundsMerc = null;

function obtenerOverlayImg() {
  if (satOverlayImg || !document.getElementById('gwRainMap')) return satOverlayImg;
  satOverlayImg = document.createElement('img');
  satOverlayImg.id = 'gwSatOverlay';
  Object.assign(satOverlayImg.style, {
    position: 'absolute', pointerEvents: 'none', opacity: '0.7', display: 'none',
  });
  document.getElementById('gwRainMap').appendChild(satOverlayImg);
  return satOverlayImg;
}

function posicionarOverlaySatelite() {
  const img = obtenerOverlayImg();
  if (!img || !satOverlayBoundsMerc || !rainMap || !esriMods) return;
  const { Point, SpatialReference } = esriMods;
  const sr = new SpatialReference({ wkid: 102100 });
  const esqSup = rainMap.toScreen(new Point(satOverlayBoundsMerc.minX, satOverlayBoundsMerc.maxY, sr));
  const esqInf = rainMap.toScreen(new Point(satOverlayBoundsMerc.maxX, satOverlayBoundsMerc.minY, sr));
  img.style.left = `${esqSup.x}px`;
  img.style.top = `${esqSup.y}px`;
  img.style.width = `${esqInf.x - esqSup.x}px`;
  img.style.height = `${esqInf.y - esqSup.y}px`;
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
  const overlay = obtenerOverlayImg();
  if (overlay) {
    const mostrarOverlay = zoom > satMaxZoom && zoom <= satOverzoomTope;
    overlay.style.display = mostrarOverlay ? 'block' : 'none';
    if (mostrarOverlay) posicionarOverlaySatelite();
  }
}

let satRetryTimer = null;
let satSinDatosSeguidos = 0;
const SAT_REINTENTO_MS = 90 * 1000;
const SAT_REINTENTOS_MAX = 3;

async function loadSatelliteLayer() {
  if (!esriMods || !rainMap) return;
  if (satRetryTimer) { clearTimeout(satRetryTimer); satRetryTimer = null; }
  const select = document.getElementById('gwSatSelect');
  const clave = select ? select.value : 'geocolor';
  const cfg = CAPAS_SATELITE[clave] || CAPAS_SATELITE.geocolor;
  satMaxZoom = cfg.maxZoom;
  satOverzoomTope = OVERZOOM_TOPE_ZOOM;

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

  const tileUrl = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${tiempo}/${cfg.tileMatrixSet}/\${level}/\${row}/\${col}.png`;

  const tileCentro = tileDeLonLat(REGION_CENTER.lon, REGION_CENTER.lat, cfg.maxZoom);
  satOverlayBoundsMerc = limitesTileMercator(tileCentro.row, tileCentro.col, cfg.maxZoom);
  const overlay = obtenerOverlayImg();
  if (overlay) {
    overlay.src = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${tiempo}/${cfg.tileMatrixSet}/${cfg.maxZoom}/${tileCentro.row}/${tileCentro.col}.png`;
  }

  function ponerCapa() {
    require(["esri/layers/WebTiledLayer"], function (WebTiledLayer) {
      if (!rainMap) return;
      if (satLayer) rainMap.removeLayer(satLayer);
      satLayer = new WebTiledLayer(tileUrl, { id: "satelite", opacity: 0.7 });
      rainMap.addLayer(satLayer);
      actualizarVisibilidadSatelite();
    });
  }

  ponerCapa();
  // Segunda pasada unos segundos despues: los tiles que ya cargaron salen
  // de la cache al instante, y los que fallaron por congestion de
  // conexiones simultaneas en la carga inicial se vuelven a pedir.
  satRetryTimer = setTimeout(() => { satRetryTimer = null; ponerCapa(); }, 4000);
}
