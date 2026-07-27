"""
Trae el historial por hora de estaciones publicas de Wunderground (no
propias) para los ultimos N dias, y lo guarda en la tabla
historial_estaciones para usarlo en el mapa de lluvias y los graficos
de detalle por estacion.

Es resumible: si se corta a la mitad, se puede volver a correr y salta
los dias que ya tiene guardados para esa estacion.

Uso (dentro del contenedor de la app, con acceso a la DB):
    python scripts/backfill_historial_wu.py
    python scripts/backfill_historial_wu.py --dias 730
    python scripts/backfill_historial_wu.py --estaciones IGUAVA3,IVLEZ2
"""
import os
import sys
import time
import argparse
import requests
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.models import db, HistorialEstacion, guardar_historial_estacion

WU_API_KEY = os.environ.get("WU_API_KEY", "")
WU_HISTORY_URL = "https://api.weather.com/v2/pws/history/hourly"

ESTACIONES_DEFAULT = ["IGUAVA3", "IBARBO1", "IBARBO2", "IVLEZ2", "IVLEZ7", "IPUENT49"]

PAUSA_ENTRE_LLAMADAS = 1.2  # segundos, para no saturar la API de WU


def dia_ya_guardado(station_id, fecha):
    inicio = datetime.combine(fecha, datetime.min.time())
    fin = inicio + timedelta(days=1)
    existe = HistorialEstacion.query.filter(
        HistorialEstacion.station_id == station_id,
        HistorialEstacion.timestamp >= inicio,
        HistorialEstacion.timestamp < fin,
    ).first()
    return existe is not None


def traer_dia(station_id, fecha):
    fecha_str = fecha.strftime("%Y%m%d")
    try:
        r = requests.get(
            WU_HISTORY_URL,
            params={"stationId": station_id, "format": "json", "units": "m",
                    "date": fecha_str, "apiKey": WU_API_KEY},
            timeout=15,
        )
    except Exception as e:
        print(f"[{station_id} {fecha_str}] Error de red: {e}")
        return 0

    if r.status_code == 204:
        return 0
    if r.status_code != 200:
        print(f"[{station_id} {fecha_str}] HTTP {r.status_code}: {r.text[:150]}")
        return 0

    observaciones = (r.json() or {}).get("observations") or []
    guardadas = 0
    for obs in observaciones:
        if guardar_historial_estacion(station_id, obs):
            guardadas += 1
    return guardadas


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dias", type=int, default=730)
    parser.add_argument("--estaciones", type=str, default=",".join(ESTACIONES_DEFAULT))
    args = parser.parse_args()

    if not WU_API_KEY:
        print("[Backfill] Falta WU_API_KEY en el entorno, no se puede continuar.")
        return

    estaciones = [e.strip() for e in args.estaciones.split(",") if e.strip()]
    hoy = datetime.utcnow().date()

    app = create_app()
    with app.app_context():
        total_filas = 0
        for station_id in estaciones:
            print(f"\n=== {station_id}: backfill de {args.dias} dias ===")
            dias_con_datos = 0
            dias_saltados = 0
            for offset in range(args.dias):
                fecha = hoy - timedelta(days=offset)

                if dia_ya_guardado(station_id, fecha):
                    dias_saltados += 1
                    continue

                filas = traer_dia(station_id, fecha)
                if filas:
                    dias_con_datos += 1
                    total_filas += filas
                    print(f"  {fecha}: {filas} horas guardadas")

                time.sleep(PAUSA_ENTRE_LLAMADAS)

            print(f"--- {station_id}: {dias_con_datos} dias con datos nuevos, "
                  f"{dias_saltados} dias ya estaban guardados ---")

        print(f"\n[Backfill] Listo. Total de filas nuevas guardadas: {total_filas}")


if __name__ == "__main__":
    main()
