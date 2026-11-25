import { test } from 'node:test';
import assert from 'node:assert/strict';
import { cargarTablero } from './tablero.mjs';

function preparar() {
  let ahora = 0;
  const ticks = [];
  const oyentes = [];
  const doc = {
    hidden: false,
    getElementById: () => null, querySelectorAll: () => [],
    addEventListener: (tipo, fn) => { if (tipo === 'visibilitychange') oyentes.push(fn); },
  };
  class Reloj extends Date { static now() { return ahora; } }
  const ctx = cargarTablero(['core.js'], {
    extra: { document: doc, Date: Reloj, setInterval: fn => { ticks.push(fn); return 0; } },
  });
  let llamadas = 0;
  ctx.cadaCiertoTiempo(() => { llamadas++; }, 1000);
  const tick = ticks.at(-1);
  return {
    doc, llamadas: () => llamadas,
    pasar(ms) { ahora += ms; tick(); },
    volver() { doc.hidden = false; oyentes.forEach(fn => fn()); },
  };
}

test('con la pestaña visible pide en cada vuelta', () => {
  const p = preparar();
  p.pasar(1000); p.pasar(1000);
  assert.equal(p.llamadas(), 2);
});

test('con la pestaña oculta no pide nada', () => {
  const p = preparar();
  p.doc.hidden = true;
  p.pasar(1000); p.pasar(1000);
  assert.equal(p.llamadas(), 0);
});

test('al volver a la pestaña actualiza una vez si ya tocaba', () => {
  const p = preparar();
  p.doc.hidden = true;
  p.pasar(1000); p.pasar(1000);
  p.volver();
  assert.equal(p.llamadas(), 1);
  p.volver();
  assert.equal(p.llamadas(), 1);
});
