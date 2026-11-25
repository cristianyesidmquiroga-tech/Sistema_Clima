// dashboard/map-defer.js — carga ArcGIS y arranca el mapa de lluvias solo
// cuando el usuario se acerca a el. ArcGIS 3.x es pesado; cargarlo de entrada
// hacia que la pagina tardara ~9s en terminar. Asi la pagina abre al instante
// y el mapa se prepara justo antes de que entre en pantalla.

(function () {
  let arrancado = false;

  function cargarArcGIS() {
    return new Promise(function (resolve) {
      if (window.require) { resolve(); return; }
      var css = document.createElement('link');
      css.rel = 'stylesheet';
      css.href = 'https://js.arcgis.com/3.28/esri/css/esri.css';
      document.head.appendChild(css);
      var s = document.createElement('script');
      s.src = 'https://js.arcgis.com/3.28/';
      s.onload = resolve;
      document.head.appendChild(s);
    });
  }

  async function arrancarMapa() {
    if (arrancado) return;
    arrancado = true;
    await cargarArcGIS();
    initRainMap();
    fetchMapaLluvias();
    cadaCiertoTiempo(fetchMapaLluvias, 90000);
    cadaCiertoTiempo(loadSatelliteLayer, 10 * 60000);
  }

  var mapEl = document.getElementById('gwRainMap');
  if (!mapEl) return;

  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (entradas, obs) {
      for (var i = 0; i < entradas.length; i++) {
        if (entradas[i].isIntersecting) { obs.disconnect(); arrancarMapa(); break; }
      }
    }, { rootMargin: '400px' });
    io.observe(mapEl);
  } else {
    arrancarMapa();
  }
})();
