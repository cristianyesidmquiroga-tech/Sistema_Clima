import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const codigo = readFileSync(new URL('../../app/static/js/dashboard/realtime.js', import.meta.url), 'utf8');

function cargar(contenido) {
  const doc = {
    getElementById: id => (id === 'lecturaInicial' && contenido !== null ? { textContent: contenido } : null),
    addEventListener() {},
  };
  const ctx = vm.createContext({ document: doc, window: {} });
  vm.runInContext(codigo, ctx);
  return ctx;
}

test('lee la lectura que viene en el html', () => {
  const ctx = cargar('{"temp_exterior": 20, "fuente": "real"}');
  assert.equal(vm.runInContext('leerLecturaInicial().temp_exterior', ctx), 20);
});

test('sin bloque en el html no hay lectura inicial', () => {
  assert.equal(vm.runInContext('leerLecturaInicial()', cargar(null)), null);
});

test('un bloque roto no rompe la pagina', () => {
  assert.equal(vm.runInContext('leerLecturaInicial()', cargar('{roto')), null);
});

test('mostrarLecturaInicial avisa si no hubo lectura para pedirla a la api', () => {
  assert.equal(vm.runInContext('mostrarLecturaInicial()', cargar(null)), false);
});
