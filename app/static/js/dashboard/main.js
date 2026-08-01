// dashboard/main.js — arranque; debe cargarse despues de todos los demas modulos

applyStoredPrefs();
fetchRealTime();
fetchHistory();
fetchForecast();
fetchAnalisisHistorico();
fetchResumenSemana();
initRainMap();
fetchMapaLluvias();

setInterval(fetchRealTime,                30_000);
setInterval(fetchHistory,           5 * 60_000);
setInterval(fetchForecast,         15 * 60_000);
setInterval(fetchAnalisisHistorico, 10 * 60_000);
setInterval(fetchResumenSemana,     10 * 60_000);
setInterval(fetchMapaLluvias,           90_000);
setInterval(loadSatelliteLayer,     10 * 60_000);  // refresca la imagen de nubes (GIBS publica cada 10 min)
