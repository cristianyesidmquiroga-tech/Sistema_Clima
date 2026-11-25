import { test } from 'node:test';
import assert from 'node:assert/strict';
import vm from 'node:vm';
import { cargarTablero } from './tablero.mjs';

function preparar() {
  const graficas = [];
  const pendientes = {};
  const lienzo = { getContext: () => ({}) };
  const ctx = cargarTablero(['core.js', 'history.js'], {
    porId: { gwHistoryChart: lienzo },
    extra: {
      Chart: class { constructor(_c, conf) { graficas.push(conf.data.labels); } destroy() {} },
      fetch: url => new Promise(r => { pendientes[url] = r; }),
    },
  });
  const responder = (url, datos, ok = true) => pendientes[url]({ ok, status: ok ? 200 : 429, json: async () => datos });
  return { ctx, graficas, responder };
}

const espera = () => new Promise(r => setImmediate(r));

test('con clics rapidos la grafica es la del ultimo boton', async () => {
  const { ctx, graficas, responder } = preparar();
  vm.runInContext("historyTipo = 'dias'", ctx);
  const dias = ctx.fetchAnalisisHistorico();
  vm.runInContext("historyTipo = 'meses'", ctx);
  const meses = ctx.fetchAnalisisHistorico();
  responder('/api/analisis?tipo=meses', [{ fecha: '2026-11', temp_avg: 20, lluvia: 3 }]);
  await meses;
  responder('/api/analisis?tipo=dias', [{ fecha: '2026-11-25', temp_avg: 21, lluvia: 1 }]);
  await dias;
  await espera();
  assert.deepEqual(graficas.map(l => [...l]), [['2026-11']]);
});

test('una respuesta de error no se pinta como datos', async () => {
  const { ctx, graficas, responder } = preparar();
  const p = ctx.fetchAnalisisHistorico();
  responder('/api/analisis?tipo=dias', { error: 'Demasiadas peticiones' }, false);
  await p;
  assert.equal(graficas.length, 0);
});
