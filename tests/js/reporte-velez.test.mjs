import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const codigo = readFileSync(new URL('../../app/static/js/reporte-velez/reporte-velez.js', import.meta.url), 'utf8');

function cargar() {
  const nodos = {};
  const nodo = () => ({ innerHTML: '', textContent: '', addEventListener() {}, querySelector: () => ({}) });
  const ctx = vm.createContext({
    document: { getElementById: id => (nodos[id] ||= nodo()) },
    window: {}, setInterval: () => 0, fetch: () => new Promise(() => {}), Date, String,
  });
  vm.runInContext(codigo, ctx);
  return { ctx, nodos };
}

const MALO = '<img src=x onerror=alert(1)>';

test('los nombres de alertas y municipios no se pintan como html', () => {
  const { ctx, nodos } = cargar();
  ctx.renderAlertas([{ nombre: MALO, nivel: 'Alerta roja' }]);
  ctx.renderMunicipios([{ municipio: MALO, nivel: { min: 1, max: 2, min_fecha: '2026-11-20', max_fecha: '2026-11-21' } }]);
  ctx.renderAnalisis([MALO]);
  for (const id of ['grvAlertas', 'grvMunicipios', 'grvAnalisis']) {
    assert.ok(!nodos[id].innerHTML.includes('<img'), id);
    assert.ok(nodos[id].innerHTML.includes('&lt;img'), id);
  }
});

test('la estacion propia sin un valor muestra -- y no undefined', () => {
  const { ctx, nodos } = cargar();
  ctx.renderEstacionPropia({ temp_max: 25 });
  assert.match(nodos.grvEstacionPropia.innerHTML, /25°C/);
  assert.ok(!nodos.grvEstacionPropia.innerHTML.includes('undefined'));
});
