"""
Cada hora manda al sellador del nodo SNA una huella con todas las lecturas
de la estacion de esa hora, para poder probar despues que no se cambiaron.
Para ver la huella de una hora: python -m scripts.sellador_horas huella 2026-11-25T14
"""
import os
import sys
from datetime import datetime, timedelta

import requests
from Crypto.Hash import keccak

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.latido import dormir, latir

APP = "clima"
INTERVALO = int(os.environ.get("SELLO_INTERVALO", "3600"))
HORAS_ATRAS = int(os.environ.get("SELLO_HORAS_ATRAS", "48"))
MARGEN = timedelta(minutes=10)


class SelladorCaido(Exception):
    pass


def config():
    valores = {n: os.environ.get(n, "") for n in ("SELLADOR_URL", "SELLADOR_SECRETO", "SELLO_SAL")}
    return valores, [n for n, v in valores.items() if not v]


def huella(texto, sal):
    sal = sal.encode("utf-8")
    if len(sal) < 32:
        raise ValueError("SELLO_SAL debe tener al menos 32 caracteres")
    return "0x" + keccak.new(digest_bits=256, data=sal + texto.encode("utf-8")).hexdigest()


def horas_pendientes(ahora, horas_atras=HORAS_ATRAS):
    ultima = (ahora - MARGEN).replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
    return [ultima - timedelta(hours=i) for i in range(horas_atras - 1, -1, -1)]


def sellar(url, secreto, h, post=requests.post):
    r = post(url.rstrip("/") + "/api/sellar", json={"app": APP, "huella": h},
             headers={"Authorization": f"Bearer {secreto}"}, timeout=30)
    if r.status_code == 200:
        return r.json()
    if r.status_code >= 500:
        raise SelladorCaido(f"HTTP {r.status_code}")
    raise RuntimeError(f"el sellador rechazo la huella: HTTP {r.status_code} {r.text[:200]}")


def sellar_pendientes(cfg, horas, lecturas_de_hora, texto_de_hora, ya, post=requests.post):
    # ya guarda las huellas confirmadas para no repetir llamadas en cada pasada.
    nuevas = 0
    for inicio in horas:
        lecturas = lecturas_de_hora(inicio)
        if not lecturas:
            continue
        h = huella(texto_de_hora(lecturas), cfg["SELLO_SAL"])
        if h in ya:
            continue
        respuesta = sellar(cfg["SELLADOR_URL"], cfg["SELLADOR_SECRETO"], h, post)
        ya.add(h)
        if not respuesta.get("yaSellada"):
            nuevas += 1
    return nuevas


def run():
    cfg, faltan = config()
    if faltan:
        print(f"[Sello] Faltan {', '.join(faltan)}; no se sella nada.")
    from app import create_app
    from app.models.sellos import lecturas_de_hora, texto_de_hora
    app = create_app()
    ya = set()
    while True:
        if not faltan:
            try:
                with app.app_context():
                    n = sellar_pendientes(cfg, horas_pendientes(datetime.utcnow()),
                                          lecturas_de_hora, texto_de_hora, ya)
                print(f"[Sello] {n} horas selladas")
                latir()
            except Exception as e:
                print(f"[Sello] Error: {e}")
        dormir(INTERVALO, latiendo=bool(faltan))


def huella_de(hora):
    cfg, faltan = config()
    if "SELLO_SAL" in faltan:
        sys.exit("Falta SELLO_SAL")
    from app import create_app
    from app.models.sellos import lecturas_de_hora, texto_de_hora
    with create_app().app_context():
        lecturas = lecturas_de_hora(datetime.strptime(hora, "%Y-%m-%dT%H"))
    print(huella(texto_de_hora(lecturas), cfg["SELLO_SAL"]))


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "huella":
        huella_de(sys.argv[2])
    else:
        run()
