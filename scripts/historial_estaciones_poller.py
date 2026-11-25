"""
Corre en bucle completando el historial por hora (tabla historial_estaciones)
de las estaciones publicas de Wunderground, para que los graficos de detalle
por estacion y el resumen de la semana siempre tengan dato reciente.

Auto-reparable: cada ciclo completa la ventana de los ultimos dias que falten,
asi una tabla vacia (despliegue nuevo) o un hueco por caida se llenan solos.
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.latido import dormir

from app import create_app
from scripts.backfill_historial_wu import traer_dia, dia_ya_guardado, ESTACIONES_DEFAULT

POLL_INTERVAL = int(os.environ.get("HISTORIAL_POLL_INTERVAL", str(30 * 60)))
VENTANA_DIAS = int(os.environ.get("HISTORIAL_VENTANA_DIAS", "8"))


def fechas_a_completar(hoy, ventana_dias, ya_guardado):
    """Dias a traer: hoy siempre (se refresca), y los anteriores de la
    ventana solo si aun no estan guardados."""
    fechas = []
    for offset in range(ventana_dias):
        fecha = hoy - timedelta(days=offset)
        if offset == 0 or not ya_guardado(fecha):
            fechas.append(fecha)
    return fechas


def run():
    app = create_app()
    if not os.environ.get("WU_API_KEY"):
        print(f"[HistorialPoller] Falta WU_API_KEY; reintento cada {POLL_INTERVAL}s.")
    print(f"[HistorialPoller] Iniciado. Estaciones={ESTACIONES_DEFAULT} ventana={VENTANA_DIAS}d intervalo={POLL_INTERVAL}s")
    while True:
        if os.environ.get("WU_API_KEY"):
            with app.app_context():
                hoy = datetime.utcnow().date()
                for station_id in ESTACIONES_DEFAULT:
                    fechas = fechas_a_completar(
                        hoy, VENTANA_DIAS, lambda f: dia_ya_guardado(station_id, f)
                    )
                    for fecha in fechas:
                        try:
                            filas = traer_dia(station_id, fecha)
                            if filas:
                                print(f"[HistorialPoller] {station_id} {fecha}: {filas} horas")
                        except Exception as e:
                            print(f"[HistorialPoller] Error {station_id} {fecha}: {e}")
        dormir(POLL_INTERVAL)


if __name__ == "__main__":
    run()
