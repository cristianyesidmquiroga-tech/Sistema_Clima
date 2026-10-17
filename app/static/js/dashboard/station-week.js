// dashboard/station-week.js — resumen de la semana en el modal de estacion

const FORMATO_DIA = { weekday: 'short', day: 'numeric', month: 'short' };

function textoDia(iso) {
  return new Date(iso + 'T12:00:00').toLocaleDateString('es-CO', FORMATO_DIA);
}

function celda(etiqueta, texto) {
  const td = document.createElement(etiqueta);
  if (texto != null) td.textContent = texto;
  return td;
}

function celdaExtremo(extremo, unidad) {
  const td = document.createElement('td');
  if (!extremo) { td.textContent = '--'; return td; }
  const valor = document.createElement('strong');
  valor.textContent = `${extremo.valor} ${unidad}`;
  const cuando = document.createElement('small');
  cuando.textContent = extremo.hora ? `${textoDia(extremo.dia)}, ${extremo.hora}` : textoDia(extremo.dia);
  td.append(valor, cuando);
  return td;
}

function filaExtremos(nombre, unidad, minimo, maximo) {
  const tr = document.createElement('tr');
  tr.append(celda('th', nombre), celdaExtremo(minimo, unidad), celdaExtremo(maximo, unidad));
  tr.firstChild.scope = 'row';
  return tr;
}

function llenarExtremos(extremos) {
  const cuerpo = document.querySelector('#gwStWeekExtremos tbody');
  cuerpo.replaceChildren(
    filaExtremos('Temperatura', '°C', extremos.temperatura.min, extremos.temperatura.max),
    filaExtremos('Humedad', '%', extremos.humedad.min, extremos.humedad.max),
    filaExtremos('Ráfaga de viento', 'km/h', null, extremos.rafaga.max),
    filaExtremos('Presión', 'hPa', extremos.presion.min, extremos.presion.max),
    filaExtremos('Índice UV', '', null, extremos.uv.max),
    filaExtremos('Día más lluvioso', 'mm', null, extremos.lluvia.dia_mas_lluvioso),
  );
}

function llenarDias(porDia) {
  const cuerpo = document.querySelector('#gwStWeekDias tbody');
  const dato = (v, u) => (v == null ? '--' : `${v}${u}`);
  cuerpo.replaceChildren(...porDia.map((d) => {
    const tr = document.createElement('tr');
    tr.append(celda('th', textoDia(d.dia)), celda('td', dato(d.temp_min, '°')), celda('td', dato(d.temp_max, '°')),
      celda('td', dato(d.humedad_min, '%')), celda('td', dato(d.humedad_max, '%')),
      celda('td', dato(d.rafaga_max, '')), celda('td', dato(d.lluvia_mm, '')));
    tr.firstChild.scope = 'row';
    return tr;
  }));
}

function avisoSemana(texto) {
  const aviso = document.getElementById('gwStWeekEstado');
  aviso.textContent = texto;
  aviso.hidden = !texto;
  document.getElementById('gwStWeekTablas').hidden = !!texto;
}

async function cargarSemanaEstacion(stationId, sigueVigente) {
  avisoSemana('Cargando la semana...');
  try {
    const res = await fetch(`/api/estacion/${stationId}/semana`);
    if (!res.ok) throw new Error(res.status);
    const resumen = await res.json();
    if (!sigueVigente()) return;
    if (!resumen.disponible) {
      avisoSemana('Esta estación no tiene datos guardados de la última semana.');
      return;
    }
    llenarExtremos(resumen.extremos);
    llenarDias(resumen.por_dia);
    document.getElementById('gwStWeekTotal').textContent =
      `Lluvia acumulada en la semana: ${resumen.extremos.lluvia.total} mm`;
    avisoSemana('');
  } catch (e) {
    if (!sigueVigente()) return;
    console.error('Error cargando la semana de la estacion', e);
    avisoSemana('No se pudo cargar la semana de esta estación.');
  }
}
