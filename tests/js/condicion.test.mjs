import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarTablero } from './tablero.mjs';

const ctx = cargarTablero(['core.js', 'realtime.js']);
const a_las = h => new Date(2026, 10, 25, h, 0);

test('si llueve de noche dice lluvia, no despejado', () => {
  assert.equal(ctx.getCondition({ lluvia_hora: '2.5' }, a_las(22)).text, 'Lluvia');
});

test('de noche sin lluvia no afirma que esta despejado', () => {
  const c = ctx.getCondition({ lluvia_hora: '0' }, a_las(23));
  assert.equal(c.fx, 'night');
  assert.ok(!c.text.includes('Despejado'));
});

test('de dia con lluvia sigue diciendo lluvia', () => {
  assert.equal(ctx.getCondition({ lluvia_hora: '1', radiacion_solar: 50 }, a_las(10)).text, 'Lluvia');
});

test('sin dato de temperatura muestra -- y no 0', () => {
  assert.equal(ctx.tempOGuion(null), '--');
  assert.equal(ctx.tempOGuion(undefined), '--');
  assert.equal(ctx.tempOGuion(0), '0.0 °C');
});
