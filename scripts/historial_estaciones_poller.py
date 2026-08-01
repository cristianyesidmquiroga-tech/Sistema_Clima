"""
Corre en bucle completando el historial por hora (tabla historial_estaciones)
de las estaciones publicas de Wunderground, para que los graficos de detalle
por estacion (modal "ultimas 24h") siempre tengan dato reciente.

Antes de este script, historial_estaciones solo se llenaba corriendo
scripts/backfill_historial_wu.py a mano - si nadie lo corria ese dia, el
modal quedaba con las graficas vacias (dias=1 sin filas recientes).
"""
import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from scripts.backfill_historial_wu import traer_dia, ESTACIONES_DEFAULT

POLL_INTERVAL = int(os.environ.get("HISTORIAL_POLL_INTERVAL", str(30 * 60)))


def run():
    if not os.environ.get("WU_API_KEY"):
        print("[HistorialPoller] Falta WU_API_KEY en el entorno, no se ejecuta.")
        return

    app = create_app()
    print(f"[HistorialPoller] Iniciado. Estaciones={ESTACIONES_DEFAULT} intervalo={POLL_INTERVAL}s")
    while True:
        with app.app_context():
            hoy = datetime.utcnow().date()
            for station_id in ESTACIONES_DEFAULT:
                try:
                    filas = traer_dia(station_id, hoy)
                    if filas:
                        print(f"[HistorialPoller] {station_id}: {filas} horas guardadas/actualizadas")
                except Exception as e:
                    print(f"[HistorialPoller] Error con {station_id}: {e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    run()
