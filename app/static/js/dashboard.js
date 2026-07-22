// ──────────────────────────────────────────────────────────────
//  dashboard.js  —  Finca Lagunitas Sistema Clima
// ──────────────────────────────────────────────────────────────

const FINCA_LAT = 5.96;
const FINCA_LON = -73.63;
const OPEN_METEO_URL = `https://api.open-meteo.com/v1/forecast?latitude=${FINCA_LAT}&longitude=${FINCA_LON}&daily=weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum&timezone=America%2FBogota&forecast_days=7`;

const WMO = {
  0:{t:'Despejado',i:'/static/icon-sun.svg'},
  1:{t:'Casi despejado',i:'/static/icon-sun.svg'},
  2:{t:'Parcialmente nublado',i:'/static/icon-cloudy.svg'},
  3:{t:'Nublado',i:'/static/icon-cloudy.svg'},
  61:{t:'Lluvia ligera',i:'/static/icon-rain.svg'},
  63:{t:'Lluvia moderada',i:'/static/icon-rain.svg'},
  65:{t:'Lluvia intensa',i:'/static/icon-rain.svg'},
  80:{t:'Chubascos',i:'/static/icon-rain.svg'},
  95:{t:'Tormenta',i:'/static/icon-rain.svg'}
};
const DAYS = ['dom','lun','mar','mié','jue','vie','sáb'];

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
function updateStatus(online) {
  els.statusDot.className = 'gw-status-dot ' + (online ? 'online' : 'offline');
  els.statusText.textContent = online ? 'Estación: En línea' : 'Estación: Desconectada';
  updateClock();
}

// ─── CONDICIÓN CLIMÁTICA ──────────────────────────────────────
function getCondition(data) {
  const h = new Date().getHours();
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
    updateStatus(true);
  } catch {
    updateStatus(false);
  }
}

function renderRealTime(data) {
  const cond = getCondition(data);
  const tempC = parseFloat(data.temp_exterior);

  els.temp.textContent      = Math.round(tempUnit === 'F' ? convertTemp(tempC) : tempC);
  els.desc.textContent      = cond.text;
  els.icon.src              = cond.icon;
  els.lluviaHoy.textContent = data.lluvia_dia;
  els.humedad.textContent   = data.humedad_exterior;
  els.viento.textContent    = data.velocidad_viento;
  els.uv.textContent        = data.uv_index ?? '--';
  els.presion.textContent   = `${data.presion_rel ?? '--'} hPa`;
  els.sensacion.textContent = `${convertTemp(data.sensacion_termica ?? data.temp_exterior)} ${tempLabel()}`;
  els.tempInt.textContent   = `${convertTemp(data.temp_interior ?? 0)} ${tempLabel()}`;
  els.rocio.textContent     = `${convertTemp(data.punto_rocio ?? 0)} ${tempLabel()}`;

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
  } catch { }
}

function getChartTextColor() {
  const container = document.querySelector('.gw-container');
  if (!container) return '#9aa0a6';
  const color = getComputedStyle(container).getPropertyValue('--text-secondary').trim();
  return color || '#9aa0a6';
}

function renderMainChart() {
  if (!historyData.length) return;
  const ctx = document.getElementById('gwChart').getContext('2d');
  if (mainChart) mainChart.destroy();

  const textColor = getChartTextColor();
  const raw    = [...historyData].reverse();
  const labels = raw.map(d => {
    const date = new Date(d.timestamp);
    return formatTime(date).split(':')[0] + ':00';
  });
  const maxTicks = Math.min(labels.length, 8);

  if (currentTab === 'temp') {
    const vals = raw.map(d => parseFloat(convertTemp(d.temp_exterior)));
    mainChart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ data: vals, borderColor: '#fbbc04',
        backgroundColor: ctx2 => {
          const g = ctx2.chart.ctx.createLinearGradient(0,0,0,130);
          g.addColorStop(0,'rgba(251,188,4,0.25)'); g.addColorStop(1,'rgba(251,188,4,0)'); return g;
        }, fill:true, tension:0.4, pointRadius:3, pointBackgroundColor:'#fbbc04', borderWidth:2 }] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} },
        scales: { x:{grid:{display:false}, ticks:{color:textColor, maxTicksLimit:maxTicks}}, y:{display:false} } }
    });

  } else if (currentTab === 'rain') {
    const vals = raw.map(d => parseFloat(d.lluvia_hora) || 0);
    mainChart = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ data: vals, backgroundColor:'rgba(138,180,248,0.75)',
        borderColor:'#8ab4f8', borderWidth:1, borderRadius:3, barPercentage:0.4, categoryPercentage:0.6 }] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} },
        scales: { x:{grid:{display:false}, ticks:{color:textColor, maxTicksLimit:maxTicks}}, y:{display:false,min:0} } }
    });

  } else {
    const vals = raw.map(d => parseFloat(d.velocidad_viento) || 0);
    mainChart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ data: vals, borderColor:'#81c995',
        backgroundColor:'rgba(129,201,149,0.08)', fill:true, tension:0.4,
        pointRadius:3, pointBackgroundColor:'#81c995', borderWidth:2 }] },
      options: { responsive:true, maintainAspectRatio:false, plugins:{ legend:{display:false} },
        scales: { x:{grid:{display:false}, ticks:{color:textColor, maxTicksLimit:maxTicks}}, y:{display:false,min:0} } }
    });
  }
}

// ─── PRONÓSTICO 7 DÍAS ────────────────────────────────────────
async function fetchForecast() {
  try {
    const res   = await fetch(OPEN_METEO_URL);
    const data  = await res.json();
    const daily = data.daily;
    els.forecastRow.innerHTML = '';

    for (let i = 0; i < 7; i++) {
      const date  = new Date(daily.time[i] + 'T12:00:00');
      const code  = daily.weathercode[i];
      const maxT  = convertTemp(daily.temperature_2m_max[i]);
      const minT  = convertTemp(daily.temperature_2m_min[i]);
      const cond  = WMO[code] || {t:'Variable',i:'/static/icon-cloudy.svg'};
      const day   = i === 0 ? 'Hoy' : DAYS[date.getDay()];

      const col = document.createElement('div');
      col.className = 'gw-day-col' + (i === 0 ? ' today' : '');
      col.innerHTML = `
        <div class="gw-day-name">${day}</div>
        <img src="${cond.i}" class="gw-day-icon" alt="${cond.t}">
        <div class="gw-day-temps">
          <span class="gw-temp-high">${Math.round(maxT)}°</span>
          <span class="gw-temp-low">${Math.round(minT)}°</span>
        </div>`;
      els.forecastRow.appendChild(col);
    }
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
    const labels  = data.map(d => d.fecha).reverse();
    const temps   = data.map(d => convertTemp(d.temp_avg)).reverse();
    const lluvias = data.map(d => d.lluvia).reverse();

    historyChart = new Chart(ctx, {
      data: { labels, datasets: [
        { type:'line', label:`Temp Prom ${tempLabel()}`, data:temps, borderColor:'#fbbc04',
          backgroundColor:'rgba(251,188,4,0.08)', fill:true, tension:0.4,
          pointRadius:3, pointBackgroundColor:'#fbbc04', yAxisID:'yLeft', borderWidth:2 },
        { type:'bar',  label:'Lluvia mm', data:lluvias,
          backgroundColor:'rgba(138,180,248,0.5)', borderRadius:3,
          barPercentage:0.5, categoryPercentage:0.6, yAxisID:'yRight' }
      ]},
      options: { responsive:true, maintainAspectRatio:false,
        plugins:{ legend:{ labels:{color:'#9aa0a6', font:{size:11}, boxWidth:12} } },
        scales: {
          x:     { grid:{display:false}, ticks:{color:'#9aa0a6', maxTicksLimit:10} },
          yLeft: { position:'left',  ticks:{color:'#fbbc04',font:{size:11}}, grid:{color:'rgba(255,255,255,0.05)'} },
          yRight:{ position:'right', ticks:{color:'#8ab4f8',font:{size:11}}, grid:{display:false} }
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
  renderMainChart(); // actualiza etiquetas del gráfico
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
