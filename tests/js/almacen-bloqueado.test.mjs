import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarTablero } from './tablero.mjs';

const bloqueado = {
  getItem() { throw new Error('SecurityError'); },
  setItem() { throw new Error('SecurityError'); },
};

test('con el almacenamiento bloqueado el tablero carga y cambia de unidad', () => {
  const ctx = cargarTablero(['core.js'], { almacen: bloqueado });
  assert.equal(ctx.tempLabel(), '°C');
  ctx.setTempUnit('F');
  assert.equal(ctx.tempLabel(), '°F');
});
