// dashboard/realtime.js — lectura en vivo, sonidos, alertas y notificaciones

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

// ─── SONIDOS DEL CLIMA (sintetizados, sin archivos externos) ──
let audioCtx = null;
function getAudioCtx() {
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();
  return audioCtx;
}

function ruidoBlanco(duracion, volumen, frecuenciaFiltro) {
  const ctx = getAudioCtx();
  const bufferSize = Math.floor(ctx.sampleRate * duracion);
  const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
  const data = buffer.getChannelData(0);
  for (let i = 0; i < bufferSize; i++) data[i] = Math.random() * 2 - 1;
  const src = ctx.createBufferSource();
  src.buffer = buffer;
  const filter = ctx.createBiquadFilter();
  filter.type = 'bandpass';
  filter.frequency.value = frecuenciaFiltro || 1200;
  const gain = ctx.createGain();
  gain.gain.setValueAtTime(volumen, ctx.currentTime);
  gain.gain.linearRampToValueAtTime(0, ctx.currentTime + duracion);
  src.connect(filter).connect(gain).connect(ctx.destination);
  src.start();
}

function tono(freq, duracion, tipo, volumen, delay) {
  const ctx = getAudioCtx();
  const osc = ctx.createOscillator();
  const gain = ctx.createGain();
  osc.type = tipo || 'sine';
  osc.frequency.value = freq;
  const t0 = ctx.currentTime + (delay || 0);
  gain.gain.setValueAtTime(0, t0);
  gain.gain.linearRampToValueAtTime(volumen, t0 + 0.05);
  gain.gain.linearRampToValueAtTime(0, t0 + duracion);
  osc.connect(gain).connect(ctx.destination);
  osc.start(t0);
  osc.stop(t0 + duracion + 0.05);
}

function sonidoLluvia()   { ruidoBlanco(2.0, 0.10, 1500); }
function sonidoTormenta() { tono(55, 1.4, 'sawtooth', 0.12, 0); ruidoBlanco(1.8, 0.09, 1200); }
function sonidoSoleado()  { tono(523, 0.25, 'sine', 0.09, 0); tono(659, 0.25, 'sine', 0.09, 0.15); tono(784, 0.4, 'sine', 0.1, 0.3); }
function sonidoNoche()    { tono(392, 0.6, 'sine', 0.06, 0); tono(523, 0.9, 'sine', 0.05, 0.35); }
function sonidoNublado()  { ruidoBlanco(1.2, 0.04, 600); tono(300, 0.8, 'sine', 0.05, 0.2); }

function reproducirSonidoClima(fx, esTormenta) {
  try {
    if (esTormenta) return sonidoTormenta();
    if (fx === 'rainy')  return sonidoLluvia();
    if (fx === 'night')  return sonidoNoche();
    if (fx === 'cloudy') return sonidoNublado();
    return sonidoSoleado();
  } catch { /* Web Audio no disponible, se ignora silenciosamente */ }
}

let sonidoInicialPendiente = true;
function intentarSonidoInicial(fx, esTormenta) {
  if (!sonidoInicialPendiente) return;
  sonidoInicialPendiente = false;
  setTimeout(() => {
    try {
      reproducirSonidoClima(fx, esTormenta);
    } catch {
      // Autoplay bloqueado por el navegador: reproducir en la primera interaccion
      const reintentar = () => { reproducirSonidoClima(fx, esTormenta); document.removeEventListener('click', reintentar); };
      document.addEventListener('click', reintentar, { once: true });
    }
  }, 1000);
}

// ─── NOTIFICACIONES DEL NAVEGADOR PARA ALERTAS ────────────────
// Maximo 2 notificaciones por tipo de alerta mientras este activa; se
// vuelve a notificar solo cuando se apaga y se activa de nuevo.
const MAX_NOTIFICACIONES_POR_ALERTA = 2;
const estadoAlertasNotificadas = new Map(); // clase -> { veces }

function notificarAlertasNuevas(alertas) {
  if (!('Notification' in window)) return;

  const clasesActivas = new Set(alertas.map(a => a.clase));
  for (const clase of estadoAlertasNotificadas.keys()) {
    if (!clasesActivas.has(clase)) estadoAlertasNotificadas.delete(clase);
  }

  const pendientes = alertas.filter(a => {
    const estado = estadoAlertasNotificadas.get(a.clase);
    return !estado || estado.veces < MAX_NOTIFICACIONES_POR_ALERTA;
  });
  if (!pendientes.length) return;

  const mostrar = () => {
    pendientes.forEach(a => {
      const estado = estadoAlertasNotificadas.get(a.clase) || { veces: 0 };
      estado.veces += 1;
      estadoAlertasNotificadas.set(a.clase, estado);
      try {
        new Notification('Sistema Clima - Región Guayaba-Bocadillo', {
          body: `${a.icono} ${a.texto}`,
          icon: '/static/img/marca/icon-192.png',
        });
      } catch { /* algunos navegadores moviles no soportan Notification en pagina */ }
    });
  };

  if (Notification.permission === 'granted') {
    mostrar();
  } else if (Notification.permission !== 'denied') {
    Notification.requestPermission().then(p => { if (p === 'granted') mostrar(); });
  }
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
    return alertas;
  }
  banner.style.display = 'flex';
  banner.innerHTML = alertas.map(a =>
    `<div class="gw-alert ${a.clase}">${a.icono} ${a.texto}</div>`
  ).join('');
  notificarAlertasNuevas(alertas);
  return alertas;
}

function renderRealTime(data) {
  const alertas = updateAlerts(data);
  const cond = getCondition(data);
  const esTormenta = alertas.some(a => a.clase === 'lluvia' || a.clase === 'viento');
  intentarSonidoInicial(cond.fx, esTormenta);
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
}
