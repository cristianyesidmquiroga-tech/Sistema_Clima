import os
import sys
import time

RUTA = os.environ.get("LATIDO_RUTA", "/tmp/latido")
PASO = 60


def latir(ruta=RUTA):
    with open(ruta, "a"):
        os.utime(ruta, None)


def dormir(segundos, ruta=RUTA, paso=PASO, esperar=time.sleep):
    # Late mientras espera, para que una espera de dias no parezca un proceso colgado.
    restante = segundos
    while restante > 0:
        latir(ruta)
        tramo = min(paso, restante)
        esperar(tramo)
        restante -= tramo
    latir(ruta)


def sano(max_segundos, ruta=RUTA, ahora=time.time):
    try:
        return ahora() - os.path.getmtime(ruta) <= max_segundos
    except OSError:
        return False


if __name__ == "__main__":
    sys.exit(0 if sano(int(sys.argv[1])) else 1)
