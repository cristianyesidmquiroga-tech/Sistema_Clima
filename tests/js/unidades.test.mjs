import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarTablero } from './tablero.mjs';

const enF = { getItem: c => (c === 'tempUnit' ? 'F' : null), setItem() {} };

test('con grados F el resumen de la semana convierte la temperatura', () => {
  const ctx = cargarTablero(['core.js', 'station-week.js'], { almacen: enF });
  const extremo = ctx.enUnidad({ valor: 20, dia: '2026-11-24', hora: '14:00' });
  assert.equal(extremo.valor, '68.0');
  assert.equal(extremo.hora, '14:00');
  assert.equal(ctx.tempLabel(), '°F');
});

test('las graficas y el mapa reciben la temperatura en la unidad elegida', () => {
  const ctx = cargarTablero(['core.js'], { almacen: enF });
  assert.equal(ctx.tempNumero(0), 32);
  assert.equal(ctx.tempNumero(null), null);
  assert.equal(ctx.tempOGuion(10), '50.0 °F');
  assert.equal(ctx.tempOGuion(null), '--');
});
