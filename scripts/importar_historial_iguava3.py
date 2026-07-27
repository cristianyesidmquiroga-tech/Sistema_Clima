"""
Copia el historial ya traido de Wunderground para la estacion propia
(IGUAVA3, guardado en historial_estaciones por el backfill) hacia la
tabla lecturas, que es la que usan el grafico de "Analisis Historico"
y las tarjetas de UV/Presion/Rocio/etc de la pagina principal.

Es resumible: salta las horas que ya tengan una lectura cercana
guardada (con passkey='historico_wu'), asi que se puede volver a
correr sin duplicar datos.

Uso (dentro del contenedor de la app):
    python scripts/importar_historial_iguava3.py
    python scripts/importar_historial_iguava3.py --estacion IGUAVA3
"""
import os
import sys
import argparse
from datetime import timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.models import db, HistorialEstacion, Lectura

MARCA_ORIGEN = "historico_wu"


def ya_importada(ts):
    ventana_inicio = ts - timedelta(minutes=5)
    ventana_fin = ts + timedelta(minutes=5)
    return db.session.query(Lectura.id).filter(
        Lectura.timestamp >= ventana_inicio,
        Lectura.timestamp <= ventana_fin,
    ).first() is not None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--estacion", type=str, default="IGUAVA3")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        filas = HistorialEstacion.query.filter_by(station_id=args.estacion).order_by(HistorialEstacion.timestamp.asc()).all()
        print(f"[Import] {len(filas)} horas encontradas en historial_estaciones para {args.estacion}")

        nuevas = 0
        saltadas = 0
        for h in filas:
            if ya_importada(h.timestamp):
                saltadas += 1
                continue

            lectura = Lectura(
                temp_exterior=h.temp_avg,
                humedad_exterior=h.humedad_avg,
                velocidad_viento=h.viento_avg,
                rafaga_viento=h.rafaga_max,
                direccion_viento=h.direccion_viento_avg,
                lluvia_dia=h.lluvia_mm,
                presion_relativa=h.presion_max,
                uv_index=int(h.uv_max) if h.uv_max is not None else None,
                radiacion_solar=h.radiacion_solar_max,
                punto_rocio=h.dewpt_avg,
                sensacion_termica=h.temp_avg,
                passkey=MARCA_ORIGEN,
            )
            lectura.timestamp = h.timestamp
            db.session.add(lectura)
            nuevas += 1

            if nuevas % 500 == 0:
                db.session.commit()
                print(f"  ...{nuevas} guardadas hasta ahora")

        db.session.commit()
        print(f"[Import] Listo. Nuevas: {nuevas}, ya existian: {saltadas}")


if __name__ == "__main__":
    main()
