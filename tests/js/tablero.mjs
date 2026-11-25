import { readFileSync } from 'node:fs';
import vm from 'node:vm';

export function elemento(atributos = {}) {
  const oyentes = {};
  const clases = new Set();
  return {
    textContent: '', src: '', style: {}, hidden: false,
    classList: {
      add: c => clases.add(c), remove: c => clases.delete(c),
      toggle: (c, si) => ((si ?? !clases.has(c)) ? clases.add(c) : clases.delete(c)),
      contains: c => clases.has(c),
    },
    getAttribute: n => atributos[n] ?? null,
    addEventListener: (tipo, fn) => { (oyentes[tipo] ||= []).push(fn); },
    disparar(tipo) { (oyentes[tipo] || []).forEach(fn => fn({ target: this, stopPropagation() {} })); },
  };
}

export function cargarTablero(archivos, { porId = {}, porSelector = {}, almacen, extra = {} } = {}) {
  const doc = {
    getElementById: id => porId[id] ?? null,
    querySelectorAll: s => porSelector[s] ?? [],
    addEventListener() {},
  };
  const ctx = vm.createContext({
    document: doc, window: {}, console, Date, Math, JSON,
    setInterval: () => 0, setTimeout: () => 0, clearTimeout() {},
    localStorage: almacen ?? { getItem: () => null, setItem() {} },
    ...extra,
  });
  for (const a of archivos) {
    vm.runInContext(readFileSync(new URL(`../../app/static/js/dashboard/${a}`, import.meta.url), 'utf8'), ctx);
  }
  return ctx;
}
