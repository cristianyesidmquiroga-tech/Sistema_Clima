// ──────────────────────────────────────────────
//  DASHBOARD - Finca Lagunitas (Mobile-First)
// ──────────────────────────────────────────────

let chartTemp, chartRain;

// Moon phase icons (0-7)
const MOON_ICONS = ['🌑', '🌒', '🌓', '🌔', '🌕', '🌖', '🌗', '🌘'];
const MOON_NAMES = ['Luna Nueva', 'Creciente Cóncava', 'Cuarto Creciente', 'Creciente Convexa', 'Luna Llena', 'Menguante Convexa', 'Cuarto Menguante', 'Menguante Cóncava'];

// Element references
const els = {
  sysDateTime: document.getElementById('sysDateTime'),
  statusBadge: document.getElementById('statusBadge'),
  statusText: document.getElementById('statusText'),
  mainWeatherIcon: document.getElementById('mainWeatherIcon'),
  
  tempExt: document.getElementById('tempExt'),
  sensacion: document.getElementById('sensacion'),
  tempMax: document.getElementById('tempMax'),
  tempMin: document.getElementById('tempMin'),
  
  humExt: document.getElementById('humExt'),
  ptoRocio: document.getElementById('ptoRocio'),
  
  vientoVel: document.getElementById('vientoVel'),
  rafaga: document.getElementById('rafaga'),
  compassArrow: document.getElementById('compassArrow'),
  
  lluvia24: document.getElementById('lluvia24'),
  lluviaHora: document.getElementById('lluviaHora'),
  
  uvIndex: document.getElementById('uvIndex'),
  uvLabel: document.getElementById('uvLabel'),
  solar: document.getElementById('solar'),
  
  presionRel: document.getElementById('presionRel'),
  presionAbs: document.getElementById('presionAbs'),
  
  tempInt: document.getElementById('tempInt'),
  humInt: document.getElementById('humInt'),
  moonIcon: document.getElementById('moonIcon'),
  moonText: document.getElementById('moonText'),
  
  analysisTextList: document.getElementById('analysisTextList')
};

// Update Date Time
setInterval(() => {
  const now = new Date();
  els.sysDateTime.textContent = now.toLocaleString('es-CO', { 
    weekday: 'short', month: 'short', day: 'numeric', 
    hour: '2-digit', minute: '2-digit' 
  });
}, 1000);

// Tab switching
function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(content => content.style.display = 'none');
  
  event.target.classList.add('active');
  document.getElementById('tab-' + tabId).style.display = 'block';
  
  if(tabId === 'analytics') {
    fetchAnalytics();
  }
}

// Fetch Realtime Data
async function fetchRealTime() {
  try {
    const res = await fetch('/api/actual');
    if (!res.ok) throw new Error("Sin datos");
    const data = await res.json();
    
    // Status
    els.statusBadge.classList.remove('offline');
    els.statusText.textContent = 'En línea';
    
    // Temperatures
    els.tempExt.textContent = data.temp_exterior;
    els.sensacion.textContent = data.sensacion_termica || data.temp_exterior;
    
    // Humidity & Dew
    els.humExt.textContent = data.humedad_exterior;
    els.ptoRocio.textContent = data.punto_rocio;
    
    // Wind
    els.vientoVel.textContent = data.velocidad_viento;
    els.rafaga.textContent = data.rafaga_viento;
    els.compassArrow.style.transform = `rotate(${data.direccion_viento}deg)`;
    
    // Rain
    els.lluvia24.textContent = data.lluvia_dia;
    els.lluviaHora.textContent = data.lluvia_hora;
    
    // UV & Solar
    els.uvIndex.textContent = data.uv_index;
    els.solar.textContent = data.radiacion_solar;
    setUvLabel(data.uv_index);
    
    // Pressure
    els.presionRel.textContent = data.presion_rel;
    els.presionAbs.textContent = data.presion_abs;
    
    // Indoor & Moon
    els.tempInt.textContent = data.temp_interior;
    els.humInt.textContent = data.humedad_interior;
    
    if(data.fase_lunar !== undefined) {
      els.moonIcon.textContent = MOON_ICONS[data.fase_lunar];
      els.moonText.textContent = MOON_NAMES[data.fase_lunar];
    }

    updateDynamicBackground(data);
    
  } catch (error) {
    els.statusBadge.classList.add('offline');
    els.statusText.textContent = 'Desconectado';
    console.error(error);
  }
}

// Set dynamic background based on weather conditions
function updateDynamicBackground(data) {
  const isNight = new Date().getHours() < 6 || new Date().getHours() > 18;
  const rain = parseFloat(data.lluvia_hora) > 0;
  const clouds = parseFloat(data.radiacion_solar) < 200 && !isNight;
  
  document.body.className = ''; // reset
  
  if (isNight) {
    document.body.classList.add('weather-bg-night');
    els.mainWeatherIcon.src = '/static/icon-night.svg'; // fallback if no svg
  } else if (rain) {
    document.body.classList.add('weather-bg-rainy');
    els.mainWeatherIcon.src = '/static/icon-rain.svg';
  } else if (clouds) {
    document.body.classList.add('weather-bg-cloudy');
    els.mainWeatherIcon.src = '/static/icon-cloudy.svg';
  } else {
    document.body.classList.add('weather-bg-sunny');
    els.mainWeatherIcon.src = '/static/icon-sun.svg';
  }
}

function setUvLabel(uv) {
  if (uv <= 2) { els.uvLabel.textContent = "Bajo"; els.uvLabel.style.color = "#69f0ae"; }
  else if (uv <= 5) { els.uvLabel.textContent = "Moderado"; els.uvLabel.style.color = "#ffd54f"; }
  else if (uv <= 7) { els.uvLabel.textContent = "Alto"; els.uvLabel.style.color = "#ffb74d"; }
  else { els.uvLabel.textContent = "Extremo"; els.uvLabel.style.color = "#ff5252"; }
}

// Fetch Daily Stats (for min/max temps)
async function fetchDailyStats() {
  try {
    const res = await fetch('/api/stats');
    const data = await res.json();
    if(data.temp_max) {
      els.tempMax.textContent = data.temp_max;
      els.tempMin.textContent = data.temp_min;
    }
  } catch(e) {}
}

// Fetch Analytics (Comparative)
async function fetchAnalytics() {
  try {
    const res = await fetch('/api/stats/comparative');
    const data = await res.json();
    
    if(data.analisis && data.analisis.length > 0) {
      els.analysisTextList.innerHTML = data.analisis.map(text => `<li>💡 ${text}</li>`).join('');
    } else {
      els.analysisTextList.innerHTML = `<li>Recopilando datos históricos para generar análisis comparativos...</li>`;
    }
  } catch(e) {
    els.analysisTextList.innerHTML = `<li>Error al cargar análisis.</li>`;
  }
}

// Charts
async function fetchCharts() {
  try {
    const res = await fetch('/api/historial');
    const data = await res.json();
    
    const labels = data.map(d => {
      const date = new Date(d.timestamp);
      return date.getHours() + ':00';
    }).reverse();
    
    const temps = data.map(d => d.temp_exterior).reverse();
    const rains = data.map(d => d.lluvia_dia).reverse();
    
    if (chartTemp) chartTemp.destroy();
    if (chartRain) chartRain.destroy();
    
    const ctxTemp = document.getElementById('chartTemp').getContext('2d');
    chartTemp = new Chart(ctxTemp, {
      type: 'line',
      data: {
        labels,
        datasets: [{
          label: 'Temp °C',
          data: temps,
          borderColor: '#fff',
          backgroundColor: 'rgba(255,255,255,0.2)',
          fill: true,
          tension: 0.4
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { display: false } },
          y: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { color: 'rgba(255,255,255,0.1)' } }
        }
      }
    });

    const ctxRain = document.getElementById('chartLluvia').getContext('2d');
    chartRain = new Chart(ctxRain, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Lluvia mm',
          data: rains,
          backgroundColor: '#82b1ff'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { display: false } },
          y: { ticks: { color: 'rgba(255,255,255,0.7)' }, grid: { color: 'rgba(255,255,255,0.1)' } }
        }
      }
    });

  } catch(e) {}
}

// Init
fetchRealTime();
fetchDailyStats();
fetchCharts();
setInterval(fetchRealTime, 30000); // 30s update
setInterval(fetchDailyStats, 60000 * 5); // 5m update
setInterval(fetchCharts, 60000 * 5); // 5m update
