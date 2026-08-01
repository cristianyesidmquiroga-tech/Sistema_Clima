function nivelFewsClase(nivel) {
  const n = (nivel || 'normal').toLowerCase();
  if (n.includes('roja')) return 'grv-alerta-roja';
  if (n.includes('naranja')) return 'grv-alerta-naranja';
  if (n.includes('amarilla')) return 'grv-alerta-amarilla';
  if (n.includes('bajo')) return 'grv-alerta-bajos';
  return 'grv-alerta-normal';
}

function renderEstacionPropia(datos) {
  const el = document.getElementById('grvEstacionPropia');
  if (!datos) {
    el.querySelector('.grv-vacio').textContent = 'Sin datos disponibles esta semana.';
    return;
  }
  el.innerHTML = `<h2>Estación propia esta semana</h2>
    <p>Temp. máx ${datos.temp_max ?? '--'}°C · Temp. mín ${datos.temp_min ?? '--'}°C ·
    Lluvia acumulada ${datos.lluvia_mm ?? '--'} mm · Viento máx ${datos.viento_max ?? '--'} km/h</p>`;
}

function renderAlertas(alertas) {
  const cont = document.getElementById('grvAlertas');
  if (!alertas || !alertas.length) {
    cont.innerHTML = '<p class="grv-vacio">Sin alertas disponibles esta semana.</p>';
    return;
  }
  cont.innerHTML = alertas.map(a => `
    <div class="grv-alerta-card ${nivelFewsClase(a.nivel)}">
      <h3>${a.nombre}</h3>
      <span class="grv-nivel">${a.nivel}</span>
    </div>`).join('');
}

const ETIQUETAS_METRICA = { nivel: 'Nivel (m)', caudal: 'Caudal (m³/s)', lluvia: 'Lluvia (mm)', temp: 'Temp. (°C)' };

function formatearFechaCorta(fechaIso) {
  if (!fechaIso) return '--';
  const [anio, mes, dia] = fechaIso.split('-');
  return new Date(anio, mes - 1, dia).toLocaleDateString('es-CO', { day: 'numeric', month: 'short' });
}

function renderMetricaMunicipio(clave, datos) {
  if (!datos) return `<div class="grv-metrica grv-metrica-vacia"><span class="grv-metrica-nombre">${ETIQUETAS_METRICA[clave]}</span><span class="grv-vacio">Sin dato</span></div>`;
  return `
    <div class="grv-metrica">
      <span class="grv-metrica-nombre">${ETIQUETAS_METRICA[clave]}</span>
      <span class="grv-metrica-valor">Mín ${datos.min} <small>(${formatearFechaCorta(datos.min_fecha)})</small></span>
      <span class="grv-metrica-valor">Máx ${datos.max} <small>(${formatearFechaCorta(datos.max_fecha)})</small></span>
    </div>`;
}

function renderMunicipios(municipios) {
  const cont = document.getElementById('grvMunicipios');
  if (!municipios || !municipios.length) {
    cont.innerHTML = '<p class="grv-vacio">Sin datos disponibles esta semana.</p>';
    return;
  }
  cont.innerHTML = municipios.map(m => `
    <div class="grv-municipio-card">
      <h3>${m.municipio}</h3>
      <div class="grv-metricas">
        ${['nivel', 'caudal', 'lluvia', 'temp'].map(clave => renderMetricaMunicipio(clave, m[clave])).join('')}
      </div>
    </div>`).join('');
}

function renderAnalisis(texto) {
  const cont = document.getElementById('grvAnalisis');
  if (!texto || !texto.length) {
    cont.innerHTML = '<p class="grv-vacio">Aún no hay suficiente historial para comparar semanas.</p>';
    return;
  }
  cont.innerHTML = texto.map(t => `<p>${t}</p>`).join('');
}

async function fetchReporteVelez() {
  try {
    const res = await fetch('/api/reporte_velez');
    const data = await res.json();
    if (!data.disponible) {
      document.getElementById('grvFechaSemana').textContent = 'Aún no se ha publicado el primer reporte semanal.';
      return;
    }
    const fecha = new Date(data.fecha_publicacion);
    document.getElementById('grvFechaSemana').textContent =
      `Semana del ${fecha.toLocaleDateString('es-CO', { day: 'numeric', month: 'long', year: 'numeric' })}`;

    const c = data.contenido || {};
    renderEstacionPropia(c.estacion_propia);
    renderAlertas(c.alertas);
    renderMunicipios(c.municipios);
    renderAnalisis(c.analisis);
  } catch (e) {
    document.getElementById('grvFechaSemana').textContent = 'No se pudo cargar el reporte, intenta de nuevo más tarde.';
  }
}

document.getElementById('grvDescargarPdf').addEventListener('click', () => {
  window.location.href = '/api/reporte_velez/pdf';
});

fetchReporteVelez();
// El reporte solo cambia una vez por semana (Principio #2), asi que
// refrescar cada hora es mas que suficiente, no hace falta polling corto.
setInterval(fetchReporteVelez, 60 * 60 * 1000);
