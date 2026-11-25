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
// Cuadro que cubre la region en cada nivel: es el que tiene que traer datos.
// Los de los bordes no sirven de prueba (el del oeste es casi todo oceano y pesa poco).
const TILE_REGION = {
  GoogleMapsCompatible_Level6: { level: 6, row: 30, col: 18 },
  GoogleMapsCompatible_Level7: { level: 7, row: 61, col: 37 },
};
const MINUTOS_ATRAS_MAX = 240;
const TANDA_HORARIOS = 6;

function horasGibsCandidatas(ahora = Date.now()) {
  // GIBS publica cada 10 min, pero a veces con mas de una hora de retraso.
  const candidatos = [];
  for (let atras = 10; atras <= MINUTOS_ATRAS_MAX; atras += 10) {
    const t = new Date(ahora - atras * 60 * 1000);
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
    // GIBS a veces responde 200 con una imagen vacia y muy chica.
    return blob.size > 2000;
  } catch (e) {
    return false;
  }
}

async function encontrarHoraValida(cfg, probar = tileTieneDatos, ahora = Date.now()) {
  const tile = TILE_REGION[cfg.tileMatrixSet];
  const candidatos = horasGibsCandidatas(ahora);
  // Del mas reciente al mas viejo, en tandas, para no lanzar decenas de pedidos a la vez.
  for (let i = 0; i < candidatos.length; i += TANDA_HORARIOS) {
    const tanda = candidatos.slice(i, i + TANDA_HORARIOS);
    const hayDatos = await Promise.all(tanda.map(t => probar(cfg, tile, t)));
    const primero = hayDatos.indexOf(true);
    if (primero >= 0) return tanda[primero];
  }
  return null;
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
// Cada carga lleva su numero; si el usuario cambia de capa mientras la anterior
// sigue buscando horario, la vieja no debe pisar a la nueva al terminar.
let satPedido = 0;

function quitarSatelite() {
  if (satLayer) rainMap.removeLayer(satLayer);
  if (satMosaico) rainMap.removeLayer(satMosaico);
  satLayer = null;
  satMosaico = null;
}

function ponerHoraSatelite(texto) {
  const horaEl = document.getElementById('gwSatHora');
  if (horaEl) horaEl.textContent = texto;
}
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
  const pedido = ++satPedido;
  ponerHoraSatelite('Buscando imagen...');

  const tiempo = await encontrarHoraValida(cfg);
  if (pedido !== satPedido) return;
  if (!tiempo) {
    console.warn('Sin horario valido de satelite NASA para esta zona ahora mismo');
    // Sin esto quedaba la capa anterior a la vista con la hora vieja.
    quitarSatelite();
    ponerHoraSatelite('Sin imagen disponible ahora, se reintenta en unos minutos');
    // GIBS a veces todavia esta procesando el horario mas reciente cuando
    // lo probamos; reintenta pronto en vez de esperar los 10 min normales.
    if (satSinDatosSeguidos < SAT_REINTENTOS_MAX) {
      satSinDatosSeguidos++;
      satRetryTimer = setTimeout(loadSatelliteLayer, SAT_REINTENTO_MS);
    }
    return;
  }
  satSinDatosSeguidos = 0;
  satMaxZoom = cfg.maxZoom;
  ponerHoraSatelite('Imagen: ' + new Date(tiempo).toLocaleTimeString(
    'es-CO', { hour: '2-digit', minute: '2-digit' }));

  const base = `https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/${cfg.layer}/default/${tiempo}/${cfg.tileMatrixSet}`;
  const tileUrl = `${base}/\${level}/\${row}/\${col}.png`;
  const urlTile = (z, row, col) => `${base}/${z}/${row}/${col}.png`;

  function ponerCapa() {
    require(["esri/layers/WebTiledLayer", "esri/layers/MapImageLayer", "esri/layers/MapImage"],
      function (WebTiledLayer, MapImageLayer, MapImage) {
        if (!rainMap || pedido !== satPedido) return;
        quitarSatelite();
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
