"""
Corre 1 vez al dia: trae la lectura actual de las 16 estaciones FEWS/IDEAM
de la Provincia de Velez y guarda 1 fila por estacion por dia en
lecturas_fews_diarias. Sin este historial diario no hay con que calcular
el minimo/maximo real por municipio (con fecha) que usa el reporte
semanal (ver scripts/publicar_reporte_velez.py) - un solo dato en vivo
por semana no alcanza para eso.
"""
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.reporte_velez import guardar_lectura_fews_diaria
from scripts.fews_ideam import consultar_lecturas_estaciones

POLL_INTERVAL = int(os.environ.get("LECTURAS_FEWS_INTERVALO", str(24 * 60 * 60)))


def capturar_hoy():
    hoy = datetime.utcnow().date()
    lecturas = consultar_lecturas_estaciones()
    guardadas = 0
    for l in lecturas:
        if all(l[campo] is None for campo in ("nivel", "caudal", "lluvia", "temp")):
            continue
        guardar_lectura_fews_diaria(
            l["station_id"], l["nombre"], l["municipio"], hoy,
            l["nivel"], l["caudal"], l["lluvia"], l["temp"],
        )
        guardadas += 1
    print(f"[LecturasFews] {guardadas} estaciones guardadas para {hoy.isoformat()}")


def run():
    app = create_app()
    print(f"[LecturasFews] Iniciado. Intervalo={POLL_INTERVAL}s")
    while True:
        with app.app_context():
            try:
                capturar_hoy()
            except Exception as e:
                print(f"[LecturasFews] Error en el ciclo: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
