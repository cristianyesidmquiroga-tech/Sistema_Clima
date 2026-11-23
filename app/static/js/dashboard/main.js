// dashboard/main.js — arranque; debe cargarse despues de todos los demas modulos

applyStoredPrefs();
fetchRealTime();
fetchHistory();
fetchForecast();
fetchAnalisisHistorico();
fetchResumenSemana();
// El mapa de lluvias y su satelite los arranca map-defer.js al acercarse el
// usuario (ArcGIS se carga diferido para que la pagina abra rapido).

setInterval(fetchRealTime,                30_000);
setInterval(fetchHistory,           5 * 60_000);
setInterval(fetchForecast,         15 * 60_000);
setInterval(fetchAnalisisHistorico, 10 * 60_000);
setInterval(fetchResumenSemana,     10 * 60_000);
