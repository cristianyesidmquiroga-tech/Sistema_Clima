// dashboard/core.js — constantes, DOM refs, formato de hora/temp, estado

const FINCA_LAT = 5.96;
const FINCA_LON = -73.63;

// ─── LIMITE DE CLICS (evita saturar el backend a punta de clicks) ─
const _contadorClicksPorKey = {};
function puedeClickear(key, maxClicks = 20, ventanaMs = 3_600_000) {
  const ahora = Date.now();
  let registro = _contadorClicksPorKey[key];
  if (!registro || ahora - registro.inicio > ventanaMs) {
    registro = { inicio: ahora, cuenta: 0 };
    _contadorClicksPorKey[key] = registro;
  }
  if (registro.cuenta >= maxClicks) return false;
  registro.cuenta++;
  return true;
}
const OPEN_METEO_URL = `https://api.open-meteo.com/v1/forecast?latitude=${FINCA_LAT}&longitude=${FINCA_LON}&hourly=temperature_2m,weathercode,relative_humidity_2m,wind_speed_10m,wind_direction_10m,precipitation_probability,precipitation&timezone=America%2FBogota&forecast_days=2`;

// Umbrales para considerar que "va a llover" en el pronostico por hora.
const LLUVIA_PROB_MIN = 50;   // %
const LLUVIA_MM_MIN   = 0.2;  // mm en esa hora

const WMO = {
  0:{t:'Despejado',i:'/static/img/mapa-estaciones/icon-sun.svg'},
  1:{t:'Casi despejado',i:'/static/img/mapa-estaciones/icon-sun.svg'},
  2:{t:'Parc. nublado',i:'/static/img/mapa-estaciones/icon-cloudy.svg'},
  3:{t:'Nublado',i:'/static/img/mapa-estaciones/icon-cloudy.svg'},
  45:{t:'Niebla',i:'/static/img/mapa-estaciones/icon-cloudy.svg'},
  48:{t:'Niebla escarcha',i:'/static/img/mapa-estaciones/icon-cloudy.svg'},
  51:{t:'Llovizna leve',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  53:{t:'Llovizna mod',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  55:{t:'Llovizna densa',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  61:{t:'Lluvia ligera',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  63:{t:'Lluvia mod',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  65:{t:'Lluvia intensa',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  80:{t:'Chubascos',i:'/static/img/mapa-estaciones/icon-rain.svg'},
  95:{t:'Tormenta',i:'/static/img/mapa-estaciones/icon-rain.svg'}
};

// ─── PREFERENCIAS (persisten en localStorage) ─────────────────
let tempUnit  = localStorage.getItem('tempUnit')  || 'C';
let timeFmt   = localStorage.getItem('timeFmt')   || '24';

// ─── ELEMENTOS DOM ────────────────────────────────────────────
const els = {
  temp:        document.getElementById('gwTemp'),
  desc:        document.getElementById('gwDesc'),
  icon:        document.getElementById('gwMainIcon'),
  lluviaHoy:   document.getElementById('gwLluviaHoy'),
  humedad:     document.getElementById('gwHumedad'),
  viento:      document.getElementById('gwViento'),
  uv:          document.getElementById('gwUV'),
  presion:     document.getElementById('gwPresion'),
  sensacion:   document.getElementById('gwSensacion'),
  tempInt:     document.getElementById('gwTempInt'),
  rocio:       document.getElementById('gwRocio'),
  luna:        document.getElementById('gwLuna'),
  solar:       document.getElementById('gwSolar'),
  dirViento:   document.getElementById('gwDirViento'),
  rafaga:      document.getElementById('gwRafaga'),
  humInt:      document.getElementById('gwHumInt'),
  statusDot:   document.getElementById('gwStatusDot'),
  statusText:  document.getElementById('gwStatusText'),
  lastUpdate:  document.getElementById('gwLastUpdate'),
  forecastRow: document.getElementById('gwForecastRow')
};

function convertTemp(celsius) {
  if (tempUnit === 'F') return ((celsius * 9/5) + 32).toFixed(1);
  return parseFloat(celsius).toFixed(1);
}
function tempLabel() { return tempUnit === 'F' ? '°F' : '°C'; }

function formatTime(date) {
  const h = date.getHours();
  const m = date.getMinutes().toString().padStart(2, '0');
  if (timeFmt === '12') {
    const ampm = h >= 12 ? 'PM' : 'AM';
    const h12  = (h % 12) || 12;
    return `${h12}:${m} ${ampm}`;
  }
  return `${h.toString().padStart(2,'0')}:${m}`;
}
function formatHour(date) {
  const h = date.getHours();
  if (timeFmt === '12') {
    const ampm = h >= 12 ? 'PM' : 'AM';
    return `${(h % 12) || 12} ${ampm}`;
  }
  return `${h.toString().padStart(2,'0')}:00`;
}

// Rejilla de horas compartida entre charts y pronostico: 16h (6 pasadas + ahora + 9 futuras)
function getDisplayHours() {
  const now = new Date();
  const hours = [];
  for (let offset = -6; offset <= 9; offset++) {
    const h = new Date(now);
    h.setHours(now.getHours() + offset, 0, 0, 0);
    hours.push(h);
  }
  return hours;
}

function updateClock() {
  const now = new Date();
  const clockTimeEl = document.getElementById('gwClockTime');
  const clockFmtEl  = document.getElementById('gwClockFmt');
  if (clockTimeEl) clockTimeEl.textContent = formatTime(now);
  if (clockFmtEl)  clockFmtEl.textContent  = timeFmt + 'h';
  if (els.lastUpdate) els.lastUpdate.textContent = formatTime(now);
}
setInterval(updateClock, 1000);

const STATUS_LABELS = {
  real: 'Estación: En línea',
  estimado: 'Estación sin señal — mostrando estimado',
  real_desactualizado: 'Estación sin señal — último dato disponible',
  offline: 'Estación: Desconectada',
};

function updateStatus(fuente) {
  const clase = fuente === 'real' ? 'online'
              : fuente === 'estimado' ? 'estimado'
              : 'offline';
  els.statusDot.className = 'gw-status-dot ' + clase;
  els.statusText.textContent = STATUS_LABELS[fuente] || STATUS_LABELS.offline;
  updateClock();
}

function getCondition(data, fecha) {
  const dt = fecha || new Date();
  const h = dt.getHours();
  const isNight  = h < 6 || h > 19;
  const hasRain  = parseFloat(data.lluvia_hora) > 0;
  const isCloudy = parseFloat(data.radiacion_solar) < 200 && !isNight;

  if (isNight)  return { text:'Despejado (noche)', icon:'/static/img/mapa-estaciones/icon-night.svg', fx:'night' };
  if (hasRain)  return { text:'Lluvia',            icon:'/static/img/mapa-estaciones/icon-rain.svg',  fx:'rainy' };
  if (isCloudy) return { text:'Nublado',           icon:'/static/img/mapa-estaciones/icon-cloudy.svg',fx:'cloudy'};
  return           { text:'Soleado',            icon:'/static/img/mapa-estaciones/icon-sun.svg',   fx:'sunny' };
}
