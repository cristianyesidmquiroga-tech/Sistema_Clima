import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const codigo = readFileSync(new URL('../../app/static/js/dashboard/realtime.js', import.meta.url), 'utf8');

function cargar(permiso) {
  const registro = { pedidos: 0, avisos: 0, audios: 0, oyentes: [] };
  class Aviso { constructor() { registro.avisos++; } static requestPermission() { registro.pedidos++; return Promise.resolve('granted'); } }
  Aviso.permission = permiso;
  class Audio { constructor() { registro.audios++; } }
  const ctx = vm.createContext({
    Notification: Aviso, window: { Notification: Aviso, AudioContext: Audio },
    document: { getElementById: () => null, addEventListener: (tipo, fn) => registro.oyentes.push(tipo) },
    setTimeout: fn => fn(), Map, Set, Math,
  });
  vm.runInContext(codigo, ctx);
  return { ctx, registro };
}

test('no pide permiso de notificaciones por su cuenta', () => {
  const { ctx, registro } = cargar('default');
  ctx.notificarAlertasNuevas([{ clase: 'lluvia', texto: 'Lluvia fuerte' }]);
  assert.equal(registro.pedidos, 0);
  assert.equal(registro.avisos, 0);
});

test('si la persona ya dio permiso, avisa', () => {
  const { ctx, registro } = cargar('granted');
  ctx.notificarAlertasNuevas([{ clase: 'lluvia', texto: 'Lluvia fuerte' }]);
  assert.equal(registro.avisos, 1);
});

test('no suena al cargar, espera el primer toque', () => {
  const { ctx, registro } = cargar('default');
  ctx.intentarSonidoInicial('sunny', false);
  assert.equal(registro.audios, 0);
  assert.deepEqual(registro.oyentes, ['pointerdown']);
});
