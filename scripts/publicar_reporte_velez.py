"""
Corre una vez por semana: calcula el minimo y el maximo real de cada
variable (nivel, caudal, lluvia, temp) por municipio a partir de las
lecturas diarias ya guardadas (ver scripts/lecturas_fews_poller.py), trae
la alerta hidrologica de rios en vivo, arma el resumen de la estacion
propia y el analisis historico, y congela todo como una fila nueva en
ReportePublicado. La ruta publica /api/reporte_velez solo lee esa fila
(cadencia semanal, ver Principio #2 del plan).

No se muestra estacion por estacion (muchas solo reportan 1-2 variables,
dejando la tabla llena de "--"): se agrupa por municipio y se muestra
minimo/maximo con la fecha y hora en que se registro cada uno, que es lo
que de verdad le sirve a alguien revisando el reporte.
"""
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.models import obtener_lecturas_rango
from app.models.reporte_velez import (
    guardar_reporte_publicado, obtener_historial_reportes_publicados,
    obtener_lecturas_fews_semana,
)
from scripts.fews_ideam import consultar_fews_alertas

PUBLICAR_INTERVALO = int(os.environ.get("REPORTE_VELEZ_INTERVALO", str(7 * 24 * 60 * 60)))
DIAS_RESUMEN_MUNICIPIOS = 7
METRICAS = ("nivel", "caudal", "lluvia", "temp")


def _resumen_municipios(dias=DIAS_RESUMEN_MUNICIPIOS):
    lecturas = obtener_lecturas_fews_semana(dias)
    por_municipio = defaultdict(list)
    for l in lecturas:
        por_municipio[l["municipio"]].append(l)

    resumen = []
    for municipio in sorted(por_municipio):
        filas = por_municipio[municipio]
        entrada = {"municipio": municipio}
        for metrica in METRICAS:
            valores = [l for l in filas if l.get(metrica) is not None]
            if not valores:
                entrada[metrica] = None
                continue
            fila_min = min(valores, key=lambda l: l[metrica])
            fila_max = max(valores, key=lambda l: l[metrica])
            entrada[metrica] = {
                "min": fila_min[metrica], "min_fecha": fila_min["fecha"],
                "max": fila_max[metrica], "max_fecha": fila_max["fecha"],
            }
        resumen.append(entrada)
    return resumen


def _resumen_estacion_propia():
    lecturas = obtener_lecturas_rango(7)
    if not lecturas:
        return None
    temps = [l["temp_exterior"] for l in lecturas if l.get("temp_exterior") is not None]
    lluvias = [l["lluvia_dia"] for l in lecturas if l.get("lluvia_dia") is not None]
    vientos = [l["velocidad_viento"] for l in lecturas if l.get("velocidad_viento") is not None]
    return {
        "temp_max": round(max(temps), 1) if temps else None,
        "temp_min": round(min(temps), 1) if temps else None,
        "lluvia_mm": round(max(lluvias), 1) if lluvias else None,
        "viento_max": round(max(vientos), 1) if vientos else None,
    }


def _analisis_historico(estacion_propia):
    anteriores = obtener_historial_reportes_publicados(limite=2)
    if len(anteriores) < 1 or not estacion_propia:
        return []
    anterior = anteriores[0]["contenido"].get("estacion_propia") or {}
    texto = []
    lluvia_actual = estacion_propia.get("lluvia_mm")
    lluvia_anterior = anterior.get("lluvia_mm")
    if lluvia_actual is not None and lluvia_anterior is not None:
        if lluvia_actual > lluvia_anterior:
            texto.append(f"Esta semana llovió más que la semana pasada ({lluvia_actual} mm vs {lluvia_anterior} mm).")
        elif lluvia_actual < lluvia_anterior:
            texto.append(f"La semana pasada llovió más que esta semana ({lluvia_anterior} mm vs {lluvia_actual} mm).")
    return texto


def publicar():
    alertas = consultar_fews_alertas()
    municipios = _resumen_municipios()
    estacion_propia = _resumen_estacion_propia()

    if alertas is None and not municipios and not estacion_propia:
        print("[ReporteVelez] Sin datos de ninguna fuente, no se publica esta semana.")
        return

    contenido = {
        "estacion_propia": estacion_propia,
        "alertas": alertas or [],
        "municipios": municipios,
        "analisis": _analisis_historico(estacion_propia),
    }
    guardar_reporte_publicado(contenido)
    print(f"[ReporteVelez] Reporte publicado en {datetime.utcnow().isoformat()}Z")


def run():
    app = create_app()
    print(f"[ReporteVelez] Iniciado. Intervalo={PUBLICAR_INTERVALO}s")
    while True:
        with app.app_context():
            try:
                publicar()
            except Exception as e:
                print(f"[ReporteVelez] Error publicando reporte: {e}")
        time.sleep(PUBLICAR_INTERVALO)


if __name__ == "__main__":
    run()
