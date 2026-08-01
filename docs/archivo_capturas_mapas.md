# Archivo histórico de capturas de mapas

## Por qué existe

Desde Fase 1 (Reporte Vélez), el sistema guarda automáticamente **una
captura diaria** de cada capa satelital (GeoColor e Infrarrojo, NASA
GOES-East) de la Provincia de Vélez. El objetivo es construir con el
tiempo un archivo histórico grande — pensado para poder comparar la zona
**por meses, años y décadas** más adelante (timelapse, comparación de
temporadas, verificación visual de eventos climáticos pasados), no solo
para la vista actual del sitio.

Guardar un PNG por día, por capa, para siempre, crecería indefinidamente
en disco. Por eso existe una política de compresión.

## Cómo funciona la política de compresión

- **Los primeros 3 meses**: cada captura queda como un archivo `.png`
  individual en `app/static/img/reporte-velez/capturas/`, para que la
  página pueda mostrar el timelapse reciente sin tener que descomprimir
  nada.
- **Pasados 3 meses**: `scripts/capturas_mapas_poller.py` agrupa por mes
  todas las capturas de esa capa que ya cumplieron los 3 meses, las
  empaqueta en un solo archivo `.zip` (uno por mes y por capa, ej.
  `satelite_geocolor_2026-05.zip`) dentro de `archivo_datos/capturas_mapas/`
  (fuera de `static/`, no se sirve directo por el navegador), y borra los
  `.png` individuales ya empaquetados.
- **Los registros en la base de datos nunca se borran.** La fila de cada
  captura (tabla `capturas_mapas`) sigue existiendo siempre; solo cambia
  el valor de `ruta_archivo` (pasa de apuntar al `.png` suelto a apuntar
  al `.zip` mensual) y `comprimido` pasa a `true`.
- Esto corre automáticamente el día 1 de cada mes, como parte del mismo
  servicio (`capturas_mapas_poller` en `docker-compose.yml`).

## Cómo ver una captura ya comprimida

Un `.zip` mensual se puede abrir con cualquier herramienta estándar, sin
necesidad de nada especial del proyecto:

**Windows**: clic derecho sobre el archivo `.zip` → "Extraer todo…".

**Línea de comandos** (Windows con Git Bash/WSL, o Linux/Mac):
```bash
unzip archivo_datos/capturas_mapas/satelite_geocolor_2026-05.zip -d /tmp/revisar_mayo
```

**Python** (si se necesita automatizar, por ejemplo para reconstruir un
timelapse de un mes viejo):
```python
import zipfile
with zipfile.ZipFile("archivo_datos/capturas_mapas/satelite_geocolor_2026-05.zip") as zf:
    zf.extractall("/tmp/revisar_mayo")
```

No hace falta ninguna contraseña ni herramienta adicional — es un `.zip`
estándar, comprimido solo para ahorrar espacio en disco, no para
restringir el acceso a la información.

## Dónde vive cada cosa

| Qué | Dónde |
|---|---|
| Capturas recientes (< 3 meses), sin comprimir | `app/static/img/reporte-velez/capturas/*.png` |
| Capturas archivadas (> 3 meses), comprimidas | `archivo_datos/capturas_mapas/*.zip` |
| Registro de cada captura (siempre, se comprima o no) | Tabla `capturas_mapas` en la base de datos |
| Lógica de captura y compresión | `scripts/capturas_mapas_poller.py` |
