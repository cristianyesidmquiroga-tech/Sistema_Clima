import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import vm from 'node:vm';

const codigo = readFileSync(new URL('../../app/static/js/dashboard/map-satellite.js', import.meta.url), 'utf8');
const ctx = vm.createContext({});
vm.runInContext(codigo, ctx);
const { tilesQueCubren } = ctx;

const MERC_MAX = Math.PI * 6378137;
const vistaVelez = { xmin: -8220000, ymin: 640000, xmax: -8180000, ymax: 680000 };

test('el mosaico cubre toda la vista, no solo un tile', () => {
  const tiles = tilesQueCubren(vistaVelez, 7);
  const xmin = Math.min(...tiles.map(t => t.extent.xmin));
  const xmax = Math.max(...tiles.map(t => t.extent.xmax));
  const ymin = Math.min(...tiles.map(t => t.extent.ymin));
  const ymax = Math.max(...tiles.map(t => t.extent.ymax));
  assert.ok(xmin <= vistaVelez.xmin && xmax >= vistaVelez.xmax);
  assert.ok(ymin <= vistaVelez.ymin && ymax >= vistaVelez.ymax);
  assert.ok(tiles.length >= 9);
});

test('los tiles no se salen del mundo', () => {
  const borde = { xmin: -MERC_MAX, ymin: MERC_MAX - 1000, xmax: -MERC_MAX + 1000, ymax: MERC_MAX };
  for (const t of tilesQueCubren(borde, 6)) {
    assert.ok(t.row >= 0 && t.col >= 0 && t.row < 64 && t.col < 64);
  }
});

test('cada tile mide lo mismo en x y en y', () => {
  const tam = (2 * MERC_MAX) / 2 ** 7;
  for (const t of tilesQueCubren(vistaVelez, 7, 0)) {
    assert.ok(Math.abs(t.extent.xmax - t.extent.xmin - tam) < 1e-6);
    assert.ok(Math.abs(t.extent.ymax - t.extent.ymin - tam) < 1e-6);
  }
});

const { horasGibsCandidatas, encontrarHoraValida } = ctx;
const AHORA = Date.UTC(2026, 10, 25, 12, 25);
const GEOCOLOR = { tileMatrixSet: 'GoogleMapsCompatible_Level7' };

test('busca horarios hasta cuatro horas atras, del mas reciente al mas viejo', () => {
  const h = horasGibsCandidatas(AHORA);
  assert.equal(h[0], '2026-11-25T12:10:00Z');
  assert.equal(h.at(-1), '2026-11-25T08:20:00Z');
  assert.equal(h.length, 24);
});

test('elige el horario mas reciente que trae datos aunque tenga mas de una hora de retraso', async () => {
  const conDatos = new Set(['2026-11-25T11:10:00Z', '2026-11-25T11:00:00Z']);
  const pedidos = [];
  const probar = async (cfg, tile, t) => { pedidos.push(t); return conDatos.has(t); };
  assert.equal(await encontrarHoraValida(GEOCOLOR, probar, AHORA), '2026-11-25T11:10:00Z');
  assert.ok(pedidos.length <= 12, 'no deberia probar todos los horarios de una vez');
});

test('solo prueba el cuadro de la region', async () => {
  const tiles = new Set();
  await encontrarHoraValida(GEOCOLOR, async (cfg, tile) => { tiles.add(`${tile.level}/${tile.row}/${tile.col}`); return false; }, AHORA);
  assert.deepEqual([...tiles], ['7/61/37']);
});

test('sin datos en cuatro horas no devuelve horario', async () => {
  assert.equal(await encontrarHoraValida(GEOCOLOR, async () => false, AHORA), null);
});

function mapaDePrueba() {
  const capas = [];
  const hora = { textContent: '' };
  const select = { value: 'geocolor' };
  class Capa { constructor(url, o = {}) { this.url = url; this.id = o.id; } setVisibility() {} }
  const c = vm.createContext({
    Date, Promise, Math, Set, console: { warn() {} },
    setTimeout: () => 0, clearTimeout() {},
    esriMods: {},
    document: { getElementById: id => (id === 'gwSatHora' ? hora : id === 'gwSatSelect' ? select : null) },
    require: (_m, cb) => cb(Capa, Capa, Capa),
  });
  c.rainMap = {
    getZoom: () => 6, extent: null,
    addLayer: l => capas.push(l),
    removeLayer: l => capas.splice(capas.indexOf(l), 1),
  };
  vm.runInContext(codigo, c);
  return { c, capas, hora, select };
}

const blobGrande = { ok: true, blob: async () => ({ size: 50000 }) };

test('si cambio de capa mientras la anterior busca, gana la que elegi', async () => {
  const { c, capas, select } = mapaDePrueba();
  let soltarGeocolor;
  const geocolorLista = new Promise(r => { soltarGeocolor = r; });
  c.fetch = async url => { if (url.includes('GeoColor')) await geocolorLista; return blobGrande; };
  const primera = c.loadSatelliteLayer();
  select.value = 'infrared';
  await c.loadSatelliteLayer();
  soltarGeocolor();
  await primera;
  const sat = capas.find(l => l.id === 'satelite');
  assert.match(sat.url, /Band13_Clean_Infrared/);
  assert.equal(capas.length, 2);
});

test('sin imagen de la capa elegida quita la anterior y lo dice', async () => {
  const { c, capas, hora, select } = mapaDePrueba();
  c.fetch = async () => blobGrande;
  await c.loadSatelliteLayer();
  assert.equal(capas.length, 2);
  select.value = 'infrared';
  c.fetch = async () => ({ ok: false });
  await c.loadSatelliteLayer();
  assert.equal(capas.length, 0);
  assert.match(hora.textContent, /Sin imagen/);
});
