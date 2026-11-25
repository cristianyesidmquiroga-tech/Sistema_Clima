import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarTablero, elemento } from './tablero.mjs';

test('las pestanas de graficas responden siempre, no solo los primeros 20 clics', () => {
  const pestanas = ['temp', 'hum', 'viento'].map(t => elemento({ 'data-target': t }));
  const filtros = ['dias', 'meses'].map(t => elemento({ 'data-tipo': t }));
  let graficas = 0, historicos = 0;
  cargarTablero(['core.js', 'ui-listeners.js'], {
    porSelector: { '.gw-tab': pestanas, '.gw-filter-btn': filtros },
    extra: { renderMainChart: () => graficas++, fetchAnalisisHistorico: () => historicos++ },
  });
  for (let i = 0; i < 30; i++) {
    pestanas[i % 3].disparar('click');
    filtros[i % 2].disparar('click');
  }
  assert.equal(graficas, 30);
  assert.equal(historicos, 30);
  assert.ok(pestanas[2].classList.contains('active'));
});
