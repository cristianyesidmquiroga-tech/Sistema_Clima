// ──────────────────────────────────────────────────────────────
//  dashboard.js  —  Finca Lagunitas Sistema Clima
// ──────────────────────────────────────────────────────────────

const FINCA_LAT = 5.96;
const FINCA_LON = -73.63;
const OPEN_METEO_URL = `https://api.open-meteo.com/v1/forecast?latitude=${FINCA_LAT}&longitude=${FINCA_LON}&hourly=temperature_2m,weathercode,relative_humidity_2m,wind_speed_10m,wind_direction_10m&timezone=America%2FBogota&forecast_days=2`;

const WMO = {
  0:{t:'Despejado',i:'/static/icon-sun.svg'},
  1:{t:'Casi despejado',i:'/static/icon-sun.svg'},
  2:{t:'Parc. nublado',i:'/static/icon-cloudy.svg'},
  3:{t:'Nublado',i:'/static/icon-cloudy.svg'},
  45:{t:'Niebla',i:'/static/icon-cloudy.svg'},
  48:{t:'Niebla escarcha',i:'/static/icon-cloudy.svg'},
  51:{t:'Llovizna leve',i:'/static/icon-rain.svg'},
  53:{t:'Llovizna mod',i:'/static/icon-rain.svg'},
  55:{t:'Llovizna densa',i:'/static/icon-rain.svg'},
  61:{t:'Lluvia ligera',i:'/static/icon-rain.svg'},
  63:{t:'Lluvia mod',i:'/static/icon-rain.svg'},
  65:{t:'Lluvia intensa',i:'/static/icon-rain.svg'},
  80:{t:'Chubascos',i:'/static/icon-rain.svg'},
  95:{t:'Tormenta',i:'/static/icon-rain.svg'}
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

// ─── CONVERSIÓN DE TEMPERATURA ────────────────────────────────
function convertTemp(celsius) {
  if (tempUnit === 'F') return ((celsius * 9/5) + 32).toFixed(1);
  return parseFloat(celsius).toFixed(1);
}
function tempLabel() { return tempUnit === 'F' ? '°F' : '°C'; }

// ─── FORMATO DE HORA ─────────────────────────────────────────
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

// ─── REJILLA DE HORAS (compartida entre charts y pronóstico) ─
function getDisplayHours() {
  const now = new Date();
  const hours = [];
  for (let offset = -6; offset <= 9; offset++) {
    const h = new Date(now);
    h.setHours(now.getHours() + offset, 0, 0, 0);
    hours.push(h);
  }
  return hours; // 16 horas: 6 pasadas + ahora + 9 futuras
}

// ─── RELOJ EN TIEMPO REAL ────────────────────────────────────
function updateClock() {
  const now = new Date();
  const clockTimeEl = document.getElementById('gwClockTime');
  const clockFmtEl  = document.getElementById('gwClockFmt');
  if (clockTimeEl) clockTimeEl.textContent = formatTime(now);
  if (clockFmtEl)  clockFmtEl.textContent  = timeFmt + 'h';
  if (els.lastUpdate) els.lastUpdate.textContent = formatTime(now);
}
setInterval(updateClock, 1000);

// ─── STATUS ───────────────────────────────────────────────────
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

// ─── CONDICIÓN CLIMÁTICA ──────────────────────────────────────
function getCondition(data, fecha) {
  const dt = fecha || new Date();
  const h = dt.getHours();
  const isNight  = h < 6 || h > 19;
  const hasRain  = parseFloat(data.lluvia_hora) > 0;
  const isCloudy = parseFloat(data.radiacion_solar) < 200 && !isNight;

  if (isNight)  return { text:'Despejado (noche)', icon:'/static/icon-night.svg', fx:'night' };
  if (hasRain)  return { text:'Lluvia',            icon:'/static/icon-rain.svg',  fx:'rainy' };
  if (isCloudy) return { text:'Nublado',           icon:'/static/icon-cloudy.svg',fx:'cloudy'};
  return           { text:'Soleado',            icon:'/static/icon-sun.svg',   fx:'sunny' };
}

// ─── TIEMPO REAL ──────────────────────────────────────────────
let lastRawData = null;

async function fetchRealTime() {
  try {
    const res = await fetch('/api/actual');
    if (!res.ok) throw new Error();
    lastRawData = await res.json();
    renderRealTime(lastRawData);

    // Integrar la lectura en vivo al historial para que la moda se actualice minuto a minuto
    if (historyData.length) {
      const ultimo = historyData[historyData.length - 1];
      const lastMin = ultimo?.timestamp?.substring(0, 16);
      const thisMin = lastRawData.timestamp?.substring(0, 16);
      if (lastMin !== thisMin) {
        historyData.push(lastRawData);
        const corte = new Date(Date.now() - 24 * 60 * 60 * 1000);
        historyData = historyData.filter(d => new Date(d.timestamp) >= corte);
      }
    }

    renderMainChart();
    renderForecastCards(); // actualizar solo las tarjetas, sin refetch Open-Meteo
    updateStatus(lastRawData.fuente || 'real');
  } catch {
    updateStatus('offline');
  }
}

const MOON_PHASES = ['🌑 Luna Nueva', '🌒 Creciente', '🌓 Cuarto Creciente', '🌔 Llena Creciente', '🌕 Luna Llena', '🌖 Llena Menguante', '🌗 Cuarto Menguante', '🌘 Menguante'];

function getWindDir(deg) {
  if (deg === undefined || deg === null) return '--';
  const val = Math.floor((deg / 22.5) + 0.5);
  const arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"];
  return arr[(val % 16)];
}

function updateFavicon(iconSrc) {
  const link = document.querySelector("link[rel='icon']");
  if (link && link.href !== location.origin + iconSrc) link.href = iconSrc;
}

// ─── ALERTAS DE CLIMA (útiles para la finca) ──────────────────
const UMBRAL_HELADA = 5;      // °C
const UMBRAL_LLUVIA = 10;     // mm/h
const UMBRAL_VIENTO = 40;     // km/h (ráfaga)

function updateAlerts(data) {
  const banner = document.getElementById('gwAlertBanner');
  if (!banner) return;

  const alertas = [];
  const temp = parseFloat(data.temp_exterior);
  const lluviaHora = parseFloat(data.lluvia_hora);
  const rafaga = parseFloat(data.rafaga_viento);

  if (!isNaN(temp) && temp <= UMBRAL_HELADA) {
    alertas.push({ clase: 'frio', icono: '❄️', texto: `Riesgo de helada: ${temp.toFixed(1)}°C` });
  }
  if (!isNaN(lluviaHora) && lluviaHora >= UMBRAL_LLUVIA) {
    alertas.push({ clase: 'lluvia', icono: '🌧️', texto: `Lluvia fuerte: ${lluviaHora.toFixed(1)} mm/h` });
  }
  if (!isNaN(rafaga) && rafaga >= UMBRAL_VIENTO) {
    alertas.push({ clase: 'viento', icono: '💨', texto: `Viento fuerte: ráfagas de ${Math.round(rafaga)} km/h` });
  }

  if (!alertas.length) {
    banner.style.display = 'none';
    banner.innerHTML = '';
    return;
  }
  banner.style.display = 'flex';
  banner.innerHTML = alertas.map(a =>
    `<div class="gw-alert ${a.clase}">${a.icono} ${a.texto}</div>`
  ).join('');
}

function renderRealTime(data) {
  updateAlerts(data);
  const cond = getCondition(data);
  const tempC = parseFloat(data.temp_exterior);

  els.temp.textContent      = Math.round(tempUnit === 'F' ? convertTemp(tempC) : tempC);
  els.desc.textContent      = cond.text;
  els.icon.src              = cond.icon;
  updateFavicon(cond.icon);
  els.lluviaHoy.textContent = data.lluvia_dia ?? 0;
  els.humedad.textContent   = data.humedad_exterior ?? '--';
  els.viento.textContent    = data.velocidad_viento ?? '--';
  
  if(els.uv) els.uv.textContent = data.uv_index ?? '--';
  if(els.presion) els.presion.textContent = `${data.presion_relativa ?? '--'} hPa`;
  if(els.sensacion) els.sensacion.textContent = `${convertTemp(data.sensacion_termica ?? data.temp_exterior)} ${tempLabel()}`;
  if(els.tempInt) els.tempInt.textContent = `${convertTemp(data.temp_interior ?? 0)} ${tempLabel()}`;
  if(els.rocio) els.rocio.textContent = `${convertTemp(data.punto_rocio ?? 0)} ${tempLabel()}`;
  
  if(els.luna) els.luna.textContent = MOON_PHASES[data.fase_lunar ?? 0];
  if(els.solar) els.solar.textContent = `${data.radiacion_solar ?? '--'} W/m²`;
  if(els.dirViento) els.dirViento.textContent = `${getWindDir(data.direccion_viento)} (${data.direccion_viento ?? '--'}°)`;
  if(els.rafaga) els.rafaga.textContent = `${data.rafaga_viento ?? '--'} km/h`;
  if(els.humInt) els.humInt.textContent = `${data.humedad_interior ?? '--'} %`;

  if (window.WeatherFX) WeatherFX.setMode(cond.fx);

  // Actualizar label de unidad debajo de la temperatura
  const unitEl = document.querySelector('.gw-unit.active');
  if (unitEl) unitEl.textContent = tempLabel();
}

// ─── HISTORIAL ────────────────────────────────────────────────
let mainChart   = null;
let historyData = [];
let currentTab  = 'temp';

async function fetchHistory() {
  try {
    const res = await fetch('/api/historial?horas=24');
    historyData = await res.json();
    renderMainChart();
    renderForecastCards(); // actualizar pronóstico con datos nuevos de estación
  } catch { }
}

function getChartTextColor() {
  const container = document.querySelector('.gw-container');
  if (!container) return '#9aa0a6';
  if (container.classList.contains('sky-sunny')) return '#0b3954';
  if (container.classList.contains('sky-cloudy')) return '#2c3e50';
  if (container.classList.contains('sky-rainy')) return '#aed6f1';
  if (container.classList.contains('sky-night')) return '#d5d8dc';
  return '#9aa0a6';
}

function moda(arr) {
  if (!arr.length) return null;
  const freq = {};
  let maxF = 0, modaVal = arr[0];
  arr.forEach(v => {
    const key = Math.round(v * 10) / 10;
    freq[key] = (freq[key] || 0) + 1;
    if (freq[key] > maxF) { maxF = freq[key]; modaVal = key; }
  });
  return modaVal;
}

function alinearPorHora(raw) {
  const now = new Date();
  const hours = getDisplayHours();
  const buckets = {};
  raw.forEach(d => {
    const dt = new Date(d.timestamp);
    const key = `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}-${dt.getHours()}`;
    if (!buckets[key]) buckets[key] = [];
    buckets[key].push(d);
  });
  const CAMPOS = ['temp_exterior','humedad_exterior','velocidad_viento','direccion_viento',
    'sensacion_termica','punto_rocio','temp_interior'];
  const result = hours.map(h => {
    const key = `${h.getFullYear()}-${h.getMonth()}-${h.getDate()}-${h.getHours()}`;
    const bucket = buckets[key];
    if (!bucket || !bucket.length) return null;
    const res = { timestamp: bucket[0].timestamp, estimado: false };
    CAMPOS.forEach(f => {
      const vals = bucket.map(d => parseFloat(d[f])).filter(v => !isNaN(v));
      if (vals.length) res[f] = moda(vals);
    });
    return res;
  });
  // Rellenar horas pasadas sin datos copiando el último valor conocido
  let ultimo = null;
  for (let i = 0; i < result.length; i++) {
    const h = hours[i];
    if (h > now) break; // dejar futuros como están (Open-Meteo)
    if (result[i]) {
      ultimo = result[i];
    } else if (ultimo) {
      // Copiar el último valor conocido y marcar como estimado
      result[i] = { ...ultimo, estimado: true };
    }
  }
  return result;
}

const TEMP_UMBRAL_C = 18;
function tempIcon(tempC) {
  const c = parseFloat(tempC);
  if (isNaN(c)) return '🌡️';
  const src = c < TEMP_UMBRAL_C ? '/static/icon-temp-cold.svg' : '/static/icon-temp-hot.svg';
  return `<img src="${src}" class="gw-wind-icon-img" alt="temp">`;
}

function obtenerOMLookup() {
  const hourly = forecastOMData?.hourly;
  const omLookup = {};
  if (hourly) {
    for (let i = 0; i < hourly.time.length; i++) {
      const dt = new Date(hourly.time[i]);
      const key = `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}-${dt.getHours()}`;
      omLookup[key] = i;
    }
  }
  return { hourly, omLookup };
}

function renderColumnCards(container, aligned, getValue, getLabel, getForecast) {
  const now = new Date();
  const nowKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}`;
  const hours = getDisplayHours();
  const { hourly, omLookup } = getForecast ? obtenerOMLookup() : { hourly: null, omLookup: {} };
  container.innerHTML = '';
  container.style.display = 'flex';
  aligned.forEach((d, i) => {
    const h = hours[i];
    const hKey = `${h.getFullYear()}-${h.getMonth()}-${h.getDate()}-${h.getHours()}`;
    const isNow = hKey === nowKey;
    let hourLabel = formatHour(h);
    let extraClass = '';
    if (isNow)                 { hourLabel = 'Ahora'; extraClass = ' today'; }
    else if (h && h < now)    extraClass = ' past';

    let pronostico = null;
    if (!d && !isNow && h > now && getForecast && hourly && omLookup[hKey] !== undefined) {
      pronostico = getForecast(hourly, omLookup[hKey]);
    }

    const col = document.createElement('div');
    col.className = 'gw-wind-col' + extraClass;
    const isEstimado = d && d.estimado;
    if (d || isNow) {
      col.innerHTML = `
        <div class="gw-wind-speed${isEstimado ? ' estimated' : ''}">${isEstimado ? '~' : ''}${getValue(d, isNow)}</div>
        <div class="gw-wind-arrow">${d ? getLabel(d, isNow) : '--'}</div>
        <div class="gw-wind-time">${hourLabel}</div>
      `;
    } else if (pronostico) {
      col.innerHTML = `
        <div class="gw-wind-speed estimated">~${pronostico.value}</div>
        <div class="gw-wind-arrow">${pronostico.label}</div>
        <div class="gw-wind-time">${hourLabel}</div>
      `;
    } else {
      col.innerHTML = `
        <div class="gw-wind-speed">--</div>
        <div class="gw-wind-arrow">--</div>
        <div class="gw-wind-time">${hourLabel}</div>
      `;
    }
    container.appendChild(col);
  });
}

function renderMainChart() {
  if (!historyData.length) return;
  const canvas = document.getElementById('gwChart');
  const windContainer = document.getElementById('gwWindContainer');

  if (mainChart) { mainChart.destroy(); mainChart = null; }

  const raw = [...historyData].reverse();
  const aligned = alinearPorHora(raw);

  if (currentTab === 'temp') {
    canvas.style.display = 'none';
    const tempNow = lastRawData ? Math.round(convertTemp(lastRawData.temp_exterior)) + '°' : null;
    renderColumnCards(windContainer, aligned, (d, isNow) => {
      if (isNow && tempNow) return tempNow;
      if (!d) return '--';
      return Math.round(parseFloat(convertTemp(d.temp_exterior))) + '°';
    }, (d, isNow) => tempIcon(isNow && tempNow ? parseFloat(lastRawData.temp_exterior) : d?.temp_exterior),
      (hourly, idx) => ({
        value: Math.round(convertTemp(hourly.temperature_2m[idx])) + '°',
        label: tempIcon(hourly.temperature_2m[idx])
      }));
  } else if (currentTab === 'rain') {
    canvas.style.display = 'none';
    const humNow = lastRawData ? Math.round(lastRawData.humedad_exterior) + '%' : null;
    renderColumnCards(windContainer, aligned, (d, isNow) => {
      if (isNow && humNow) return humNow;
      if (!d) return '--';
      return Math.round(parseFloat(d.humedad_exterior) || 0) + '%';
    }, d => '💧',
      (hourly, idx) => ({
        value: Math.round(hourly.relative_humidity_2m[idx]) + '%',
        label: '💧'
      }));
  } else if (currentTab === 'wind') {
    canvas.style.display = 'none';
    const windNow = lastRawData ? Math.round(lastRawData.velocidad_viento) + ' km/h' : null;
    renderColumnCards(windContainer, aligned, (d, isNow) => {
      if (isNow && windNow) return windNow;
      if (!d) return '--';
      return Math.round(parseFloat(d.velocidad_viento) || 0) + ' km/h';
    }, d => '↓',
      (hourly, idx) => ({
        value: Math.round(hourly.wind_speed_10m[idx]) + ' km/h',
        label: '↓'
      }));
    const { hourly, omLookup } = obtenerOMLookup();
    const hours = getDisplayHours();
    const arrows = windContainer.querySelectorAll('.gw-wind-arrow');
    aligned.forEach((d, i) => {
      if (!arrows[i]) return;
      if (d) {
        arrows[i].style.transform = `rotate(${parseFloat(d.direccion_viento) || 0}deg)`;
      } else if (hourly) {
        const h = hours[i];
        const key = `${h.getFullYear()}-${h.getMonth()}-${h.getDate()}-${h.getHours()}`;
        if (omLookup[key] !== undefined) {
          arrows[i].style.transform = `rotate(${hourly.wind_direction_10m[omLookup[key]] || 0}deg)`;
        }
      }
    });
  }
}

// ─── PRONÓSTICO POR HORAS (pasado + presente + futuro) ──────
// Cache de Open-Meteo (se refresca cada 15 min)
let forecastOMData = null;
let forecastOMTs = 0;
const FORECAST_CACHE_MS = 15 * 60 * 1000;

function renderForecastCards() {
  const now = new Date();
  const displayHours = getDisplayHours();
  const nowKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}`;

  // Datos de estación alineados por hora (con estimaciones)
  let estacionAlineados = [];
  if (historyData.length) {
    const raw = [...historyData].reverse();
    estacionAlineados = alinearPorHora(raw);
  }

  const hourly = forecastOMData?.hourly;
  const omLookup = {};
  if (hourly) {
    for (let i = 0; i < hourly.time.length; i++) {
      const dt = new Date(hourly.time[i]);
      const key = `${dt.getFullYear()}-${dt.getMonth()}-${dt.getDate()}-${dt.getHours()}`;
      omLookup[key] = i;
    }
  }

  const ultimoReal = estacionAlineados.filter(d => d && !d.estimado).pop() || null;
  els.forecastRow.innerHTML = '';

  displayHours.forEach((h, i) => {
    const key = `${h.getFullYear()}-${h.getMonth()}-${h.getDate()}-${h.getHours()}`;
    let hourStr = formatHour(h);
    let extraClass = '';
    if (key === nowKey)      { hourStr = 'Ahora'; extraClass = ' today'; }
    else if (h < now)        extraClass = ' past';

    let temp = null;
    let cond = {t:'--',i:'/static/icon-cloudy.svg'};
    let esEstimado = false;

    if (key === nowKey && lastRawData) {
      temp = convertTemp(lastRawData.temp_exterior);
      const liveCond = getCondition(lastRawData);
      cond = {t: liveCond.text, i: liveCond.icon};
    } else if (h < now && estacionAlineados[i]) {
      const d = estacionAlineados[i];
      if (d.temp_exterior !== undefined) temp = convertTemp(d.temp_exterior);
      esEstimado = d.estimado;
      if (ultimoReal) {
        const c = getCondition(ultimoReal, new Date(h));
        cond = {t: c.text, i: c.icon};
      }
    } else if (omLookup[key] !== undefined) {
      const idx = omLookup[key];
      temp = convertTemp(hourly.temperature_2m[idx]);
      const code = hourly.weathercode[idx];
      cond = code !== null ? (WMO[code] || {t:'Variable',i:'/static/icon-cloudy.svg'}) : {t:'--',i:'/static/icon-cloudy.svg'};
      const esNoche = h.getHours() < 6 || h.getHours() > 19;
      if (esNoche && cond.i === '/static/icon-sun.svg') {
        cond = { t: cond.t, i: '/static/icon-night.svg' };
      }
    }

    const col = document.createElement('div');
    col.className = 'gw-day-col' + (esEstimado ? ' estimated' : '') + extraClass;
    col.innerHTML = `
      <div class="gw-day-name">${hourStr}</div>
      <img src="${cond.i}" class="gw-day-icon" alt="${cond.t}">
      <div class="gw-day-temps">
        <span class="gw-temp-high">${esEstimado ? '~' : ''}${temp !== null ? Math.round(temp) + '°' : '--'}</span>
      </div>`;
    els.forecastRow.appendChild(col);
  });
}

async function fetchForecast() {
  try {
    // Refrescar Open-Meteo cada 15 min
    if (!forecastOMData || Date.now() - forecastOMTs > FORECAST_CACHE_MS) {
      const res = await fetch(OPEN_METEO_URL);
      forecastOMData = await res.json();
      forecastOMTs = Date.now();
    }
    renderForecastCards();
  } catch {
    els.forecastRow.innerHTML = '<p style="color:var(--text-secondary);font-size:13px;">Pronóstico no disponible</p>';
  }
}

// ─── ANÁLISIS HISTÓRICO ───────────────────────────────────────
let historyChart = null;
let historyTipo  = 'dias';

async function fetchAnalisisHistorico() {
  try {
    const res  = await fetch(`/api/analisis?tipo=${historyTipo}`);
    const data = await res.json();
    const ctx  = document.getElementById('gwHistoryChart').getContext('2d');
    if (historyChart) historyChart.destroy();
    if (!data.length) return;

    const textColor = getChartTextColor();
    
    // Generar análisis de texto
    const analysisEl = document.getElementById('gwHistoryAnalysis');
    if (analysisEl) {
      if (data.length > 0) {
        let sumTemp = 0, maxTemp = -999, minTemp = 999;
        let sumLluvia = 0;
        data.forEach(d => {
          const t = parseFloat(d.temp_avg) || 0;
          sumTemp += t;
          if(t > maxTemp) maxTemp = t;
          if(t < minTemp) minTemp = t;
          sumLluvia += parseFloat(d.lluvia) || 0;
        });
        const avgTemp = (sumTemp / data.length).toFixed(1);
        sumLluvia = sumLluvia.toFixed(1);
        
        let labelTipo = historyTipo === 'dias' ? 'los últimos días' : (historyTipo === 'meses' ? 'los últimos meses' : 'los últimos años');
        
        analysisEl.innerHTML = `
          <strong>Análisis de ${labelTipo}:</strong><br>
          🌡️ Temp. Promedio: ${avgTemp}°C (Máx: ${maxTemp.toFixed(1)}°C, Mín: ${minTemp.toFixed(1)}°C)<br>
          🌧️ Lluvia Acumulada: ${sumLluvia} mm
        `;
        analysisEl.style.display = 'block';
      } else {
        analysisEl.style.display = 'none';
      }
    }

    const labels  = data.map(d => d.fecha).reverse();
    const temps   = data.map(d => convertTemp(d.temp_avg)).reverse();
    const lluvias = data.map(d => d.lluvia).reverse();

    historyChart = new Chart(ctx, {
      data: { labels, datasets: [
        { type:'line', label:`Temp Prom ${tempLabel()}`, data:temps, borderColor:'#fbbc04',
          backgroundColor:'rgba(251,188,4,0.08)', fill:true, tension:0.4,
          pointRadius:3, pointBackgroundColor:'#fbbc04', yAxisID:'yLeft', borderWidth:2 },
        { type:'line', label:'Lluvia mm', data:lluvias,
          borderColor:'#8ab4f8', backgroundColor:'rgba(138,180,248,0.35)',
          fill:true, tension:0.4, pointRadius:3, pointBackgroundColor:'#8ab4f8',
          borderWidth:2, yAxisID:'yRight' }
      ]},
      options: { responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ labels:{color:'rgba(255,255,255,0.9)', font:{size:11, weight:'500'}, boxWidth:12} } },
        scales: {
          x:     { grid:{display:false}, ticks:{color:'rgba(255,255,255,0.9)', font:{weight:'500'}, maxTicksLimit:10} },
          yLeft: { position:'left',  ticks:{color:'#fbbc04',font:{size:11, weight:'500'}}, grid:{color:'rgba(255,255,255,0.05)'} },
          yRight:{ position:'right', ticks:{color:'#8ab4f8',font:{size:11, weight:'500'}}, grid:{display:false} }
        }
      }
    });
  } catch { }
}

// ─── LISTENERS ───────────────────────────────────────────────
document.querySelectorAll('.gw-tab').forEach(btn => {
  btn.addEventListener('click', e => {
    document.querySelectorAll('.gw-tab').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    currentTab = e.target.getAttribute('data-target');
    renderMainChart();
  });
});

document.querySelectorAll('.gw-filter-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    document.querySelectorAll('.gw-filter-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    historyTipo = e.target.getAttribute('data-tipo');
    fetchAnalisisHistorico();
  });
});

// Clic en °C (inline en la temperatura grande)
const unitCEl = document.getElementById('unitC');
const unitFEl = document.getElementById('unitF');
if (unitCEl) unitCEl.addEventListener('click', () => switchTempUnit('C'));
if (unitFEl) unitFEl.addEventListener('click', () => switchTempUnit('F'));

// También los botones del header si existen
document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(btn => {
  btn.addEventListener('click', e => switchTempUnit(e.target.getAttribute('data-unit')));
});

function switchTempUnit(unit) {
  tempUnit = unit;
  localStorage.setItem('tempUnit', tempUnit);
  // Actualizar estado visual de todos los controles
  if (unitCEl) unitCEl.classList.toggle('active', unit === 'C');
  if (unitFEl) unitFEl.classList.toggle('active', unit === 'F');
  document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(b =>
    b.classList.toggle('active', b.getAttribute('data-unit') === unit)
  );
  if (lastRawData) renderRealTime(lastRawData);
  renderMainChart();
  fetchForecast();
  fetchAnalisisHistorico();
}

// Clic en el reloj (inline) para cambiar formato de hora
const clockEl = document.getElementById('gwClock');
if (clockEl) clockEl.addEventListener('click', () => {
  timeFmt = timeFmt === '24' ? '12' : '24';
  localStorage.setItem('timeFmt', timeFmt);
  document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(b =>
    b.classList.toggle('active', b.getAttribute('data-fmt') === timeFmt)
  );
  updateClock();
  renderMainChart();
  fetchForecast(); // actualizar etiquetas de horas en el pronóstico
});

// También los botones del header si existen
document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(b => b.classList.remove('active'));
    e.target.classList.add('active');
    timeFmt = e.target.getAttribute('data-fmt');
    localStorage.setItem('timeFmt', timeFmt);
    updateClock();
    renderMainChart();
    fetchForecast(); // re-renderizar tarjetas del pronóstico con el nuevo formato
  });
});

// Aplicar preferencias guardadas al cargar
function applyStoredPrefs() {
  document.querySelectorAll('#tempToggle .gw-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-unit') === tempUnit);
  });
  document.querySelectorAll('#timeToggle .gw-toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.getAttribute('data-fmt') === timeFmt);
  });
}

// ─── POPOVER INFO ─────────────────────────────────────────────
document.querySelectorAll('.gw-info-btn').forEach(btn => {
  btn.addEventListener('click', e => {
    e.stopPropagation();
    const wasActive = btn.classList.contains('active');
    document.querySelectorAll('.gw-info-btn.active').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.gw-info-popover.show').forEach(p => p.classList.remove('show'));
    if (!wasActive) {
      btn.classList.add('active');
      btn.closest('.gw-extra-card').querySelector('.gw-info-popover').classList.add('show');
    }
  });
});
document.addEventListener('click', () => {
  document.querySelectorAll('.gw-info-btn.active').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.gw-info-popover.show').forEach(p => p.classList.remove('show'));
});

// ─── ARRANQUE ─────────────────────────────────────────────────
applyStoredPrefs();
fetchRealTime();
fetchHistory();
fetchForecast();
fetchAnalisisHistorico();

setInterval(fetchRealTime,                30_000);
setInterval(fetchHistory,           5 * 60_000);
setInterval(fetchForecast,         15 * 60_000);
setInterval(fetchAnalisisHistorico, 10 * 60_000);
