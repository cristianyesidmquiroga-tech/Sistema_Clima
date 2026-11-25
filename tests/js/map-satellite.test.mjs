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
