import math
import os
from datetime import datetime, timezone

import redis

# La llave gratuita de WU da 1500 consultas al dia; se reparte entre quienes la usan.
CUOTAS = {"estacion": 750, "mapa": 400, "historial": 250}
DIA = 86400


def disponibles(cuota, segundos_del_dia):
    # Solo se gasta lo que corresponde a la hora: la cuota alcanza hasta medianoche.
    return math.floor(cuota * segundos_del_dia / DIA) + 1


def _cliente():
    url = os.environ.get("REDIS_URL")
    if not url:
        return None
    return redis.Redis.from_url(url, socket_timeout=2)


def tomar(consumidor, ahora=None, cliente=None):
    ahora = ahora or datetime.now(timezone.utc)
    cliente = cliente if cliente is not None else _cliente()
    if cliente is None:
        return True
    clave = f"wu:{consumidor}:{ahora:%Y-%m-%d}"
    segundos = ahora.hour * 3600 + ahora.minute * 60 + ahora.second
    try:
        usadas = cliente.incr(clave)
        if usadas == 1:
            cliente.expire(clave, 2 * DIA)
        if usadas > disponibles(CUOTAS[consumidor], segundos):
            cliente.decr(clave)
            return False
    except (redis.RedisError, OSError) as e:
        # Sin Redis se consulta igual: perder datos es peor que pasarse un poco.
        print(f"[CuotaWU] Sin contador ({e}); consulto igual.")
    return True
