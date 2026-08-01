// dashboard/history.js — historial, grafica principal, pronostico y analisis

let mainChart   = null;
let historyData = [];
let currentTab  = 'temp';

async function fetchHistory() {
  try {
    const res = await fetch('/api/historial?horas=24');
    historyData = await res.json();
    renderMainChart();
    renderForecastCards(); // actualizar pronostico con datos nuevos de estacion
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
  // Rellenar horas pasadas sin datos copiando el ultimo valor conocido
  let ultimo = null;
  for (let i = 0; i < result.length; i++) {
    const h = hours[i];
    if (h > now) break; // dejar futuros como estan (Open-Meteo)
    if (result[i]) {
      ultimo = result[i];
    } else if (ultimo) {
      result[i] = { ...ultimo, estimado: true };
    }
  }
  return result;
}

const TEMP_UMBRAL_C = 18;
function tempIcon(tempC) {
  const c = parseFloat(tempC);
  if (isNaN(c)) return '🌡️';
  const src = c < TEMP_UMBRAL_C ? '/static/img/mapa-estaciones/icon-temp-cold.svg' : '/static/img/mapa-estaciones/icon-temp-hot.svg';
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

// ─── PRONOSTICO POR HORAS (pasado + presente + futuro) ──────
let forecastOMData = null;
let forecastOMTs = 0;
const FORECAST_CACHE_MS = 15 * 60 * 1000;

function renderForecastCards() {
  const now = new Date();
  const displayHours = getDisplayHours();
  const nowKey = `${now.getFullYear()}-${now.getMonth()}-${now.getDate()}-${now.getHours()}`;

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
    let cond = {t:'--',i:'/static/img/mapa-estaciones/icon-cloudy.svg'};
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
      let code = hourly.weathercode[idx];
      const pop = hourly.precipitation_probability ? hourly.precipitation_probability[idx] : null;
      const mm  = hourly.precipitation ? hourly.precipitation[idx] : null;
      const esCodigoLluvia = code !== null && code >= 51;
      const lluviaConfirmada = pop === null || mm === null
        ? esCodigoLluvia
        : (pop >= LLUVIA_PROB_MIN && mm >= LLUVIA_MM_MIN);
      if (esCodigoLluvia && !lluviaConfirmada) code = 2; // baja a "Parc. nublado", no alcanza el umbral
      cond = code !== null ? (WMO[code] || {t:'Variable',i:'/static/img/mapa-estaciones/icon-cloudy.svg'}) : {t:'--',i:'/static/img/mapa-estaciones/icon-cloudy.svg'};
      const esNoche = h.getHours() < 6 || h.getHours() > 19;
      if (esNoche && cond.i === '/static/img/mapa-estaciones/icon-sun.svg') {
        cond = { t: cond.t, i: '/static/img/mapa-estaciones/icon-night.svg' };
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

// ─── ANALISIS HISTORICO ───────────────────────────────────────
let historyChart = null;
let historyTipo  = 'dias';

// Resumen semanal con extremos reales (no el promedio de promedios diarios)
async function fetchResumenSemana() {
  const analysisEl = document.getElementById('gwHistoryAnalysis');
  if (!analysisEl) return;
  try {
    const res = await fetch('/api/analisis/semana');
    const r = await res.json();
    if (r.temp_max == null) { analysisEl.style.display = 'none'; return; }

    const tMax = convertTemp(r.temp_max), tMin = convertTemp(r.temp_min), tAvg = convertTemp(r.temp_avg);
    const u = tempLabel();

    analysisEl.innerHTML = `
      <strong>Análisis de la última semana:</strong><br>
      🌡️ Temp: Prom ${tAvg}${u} (Máx: ${tMax}${u}, Mín: ${tMin}${u})<br>
      💧 Humedad: Máx ${r.humedad_max ?? '--'}%, Mín ${r.humedad_min ?? '--'}%<br>
      💨 Viento: Máx ${r.viento_max ?? '--'} km/h, Mín ${r.viento_min ?? '--'} km/h<br>
      🌧️ Lluvia Acumulada: ${r.lluvia_semana ?? '--'} mm
    `;
    analysisEl.style.display = 'block';
  } catch (e) {
    console.error('Error cargando resumen semanal', e);
  }
}

async function fetchAnalisisHistorico() {
  try {
    const res  = await fetch(`/api/analisis?tipo=${historyTipo}`);
    const data = await res.json();
    const ctx  = document.getElementById('gwHistoryChart').getContext('2d');
    if (historyChart) historyChart.destroy();
    if (!data.length) return;

    const textColor = getChartTextColor();

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
