"""
Guarda 1 captura diaria de cada capa satelital (GeoColor e Infrarrojo,
NASA GOES-East / GIBS) para la Provincia de Velez, para ir armando un
archivo historico que en Fase 1+ sirve para un timelapse ("la tierra
desde el espacio") y para verificar visualmente el analisis que ya se
hace con datos numericos de las estaciones (propia + las 16 de IDEAM).

Fetch siempre server-side (Principio #1) - el navegador nunca ve la URL
de GIBS, solo la imagen final guardada en /static/img/reporte-velez/capturas/.

Politica de almacenamiento (decidida explicitamente por el equipo, ver
docs/archivo_capturas_mapas.md para el detalle completo):
- Los primeros 3 meses, cada captura queda como PNG individual (para que
  el timelapse mas reciente sea rapido de armar).
- Pasados 3 meses, las capturas de un mismo mes se comprimen en un solo
  .zip mensual y se borran los PNG individuales - los registros en la
  base de datos nunca se eliminan, solo cambia donde vive el archivo
  (ver marcar_capturas_comprimidas en app/models/reporte_velez.py).
"""
import os
import sys
import time
import zipfile
import requests
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.reporte_velez import (
    guardar_captura_mapa, obtener_capturas_pendientes_de_comprimir,
    marcar_capturas_comprimidas,
)

CAPTURA_INTERVALO = int(os.environ.get("CAPTURAS_MAPAS_INTERVALO", str(24 * 60 * 60)))
DIAS_ANTES_DE_COMPRIMIR = 90

# Mismos layer/tileMatrixSet/tile de referencia que ya usa y tiene
# verificado el mapa de estaciones (ver CAPAS_SATELITE y TILES_REGION en
# app/static/js/dashboard/map-satellite.js) - el zoom y el tile deben
# coincidir con el tileMatrixSet exacto, cada set tiene su propia
# cuadricula nativa.
MAPA = "reporte-velez"
CAPAS_SATELITE = {
    "satelite_geocolor": {
        "layer": "GOES-East_ABI_GeoColor", "tileMatrixSet": "GoogleMapsCompatible_Level7",
        "zoom": 7, "row": 61, "col": 37,
    },
    "satelite_infrarrojo": {
        "layer": "GOES-East_ABI_Band13_Clean_Infrared", "tileMatrixSet": "GoogleMapsCompatible_Level6",
        "zoom": 6, "row": 30, "col": 18,
    },
}

DIR_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_CAPTURAS = os.path.join(DIR_BASE, "app", "static", "img", "reporte-velez", "capturas")
DIR_ARCHIVO_COMPRIMIDO = os.path.join(DIR_BASE, "archivo_datos", "capturas_mapas")


def _tile_url(cfg, tiempo):
    return (
        f"https://gibs.earthdata.nasa.gov/wmts/epsg3857/best/{cfg['layer']}/default/"
        f"{tiempo}/{cfg['tileMatrixSet']}/{cfg['zoom']}/{cfg['row']}/{cfg['col']}.png"
    )


def _horas_gibs_candidatas():
    """GIBS publica cada 10 min pero con retraso de procesamiento
    variable; se prueban varios horarios recientes y se usa el primero
    con datos reales (mismo enfoque que encontrarHoraValida() en
    map-satellite.js, reimplementado server-side)."""
    candidatos = []
    for atras in range(20, 90, 10):
        t = datetime.utcnow() - timedelta(minutes=atras)
        t = t.replace(second=0, microsecond=0)
        t = t.replace(minute=(t.minute // 10) * 10)
        candidatos.append(t.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return candidatos


def _capturar_capa(nombre_capa, cfg, fecha):
    contenido = None
    for tiempo in _horas_gibs_candidatas():
        try:
            r = requests.get(_tile_url(cfg, tiempo), timeout=15)
            if r.status_code == 200 and len(r.content) > 2000:
                contenido = r.content
                break
        except Exception:
            continue

    if contenido is None:
        print(f"[CapturasMapas] {nombre_capa}: sin horario con datos reales disponible hoy, se omite")
        return

    os.makedirs(DIR_CAPTURAS, exist_ok=True)
    nombre_archivo = f"{nombre_capa}_{fecha.isoformat()}.png"
    ruta_absoluta = os.path.join(DIR_CAPTURAS, nombre_archivo)
    with open(ruta_absoluta, "wb") as f:
        f.write(contenido)
    ruta_relativa = f"/static/img/reporte-velez/capturas/{nombre_archivo}"
    guardar_captura_mapa(MAPA, nombre_capa, fecha, ruta_relativa)
    print(f"[CapturasMapas] {nombre_capa}: guardada {ruta_relativa}")


def capturar_hoy():
    hoy = datetime.utcnow().date()
    for nombre_capa, cfg in CAPAS_SATELITE.items():
        _capturar_capa(nombre_capa, cfg, hoy)


def comprimir_capturas_viejas():
    """Agrupa por mes las capturas con mas de 3 meses y las empaqueta en
    un .zip, liberando espacio de los PNG individuales sin perder el
    dato (ver docs/archivo_capturas_mapas.md)."""
    for nombre_capa in CAPAS_SATELITE:
        pendientes = obtener_capturas_pendientes_de_comprimir(MAPA, nombre_capa, DIAS_ANTES_DE_COMPRIMIR)
        if not pendientes:
            continue
        por_mes = defaultdict(list)
        for captura in pendientes:
            mes = captura["fecha_captura"][:7]  # YYYY-MM
            por_mes[mes].append(captura)

        os.makedirs(DIR_ARCHIVO_COMPRIMIDO, exist_ok=True)
        for mes, capturas in por_mes.items():
            nombre_zip = f"{nombre_capa}_{mes}.zip"
            ruta_zip = os.path.join(DIR_ARCHIVO_COMPRIMIDO, nombre_zip)
            fechas = []
            with zipfile.ZipFile(ruta_zip, "a", zipfile.ZIP_DEFLATED) as zf:
                for captura in capturas:
                    ruta_png = os.path.join(DIR_BASE, captura["ruta_archivo"].lstrip("/"))
                    if os.path.exists(ruta_png):
                        zf.write(ruta_png, arcname=os.path.basename(ruta_png))
                        os.remove(ruta_png)
                    fechas.append(captura["fecha_captura"])
            marcar_capturas_comprimidas(MAPA, nombre_capa, fechas, f"archivo_datos/capturas_mapas/{nombre_zip}")
            print(f"[CapturasMapas] Comprimidas {len(fechas)} capturas de {nombre_capa} ({mes}) en {nombre_zip}")


def run():
    app = create_app()
    print(f"[CapturasMapas] Iniciado. Intervalo={CAPTURA_INTERVALO}s")
    ultimo_dia_compresion = None
    while True:
        with app.app_context():
            try:
                capturar_hoy()
                hoy = datetime.utcnow().date()
                if hoy.day == 1 and ultimo_dia_compresion != hoy:
                    comprimir_capturas_viejas()
                    ultimo_dia_compresion = hoy
            except Exception as e:
                print(f"[CapturasMapas] Error en el ciclo: {e}")
        time.sleep(CAPTURA_INTERVALO)


if __name__ == "__main__":
    run()
