from datetime import datetime, timezone

import pytest

from scripts import wu_poller


class Respuesta:
    def __init__(self, codigo, texto, datos=None):
        self.status_code, self.text, self._datos = codigo, texto, datos

    def json(self):
        return self._datos


def test_llave_limitada_se_distingue_de_otros_errores(monkeypatch):
    monkeypatch.setattr(wu_poller.requests, 'get', lambda *a, **k: Respuesta(401, 'API key is throttled'))
    with pytest.raises(wu_poller.LlaveLimitada):
        wu_poller.fetch_wu()


def test_otro_error_de_wu_devuelve_none(monkeypatch):
    monkeypatch.setattr(wu_poller.requests, 'get', lambda *a, **k: Respuesta(500, 'caido'))
    assert wu_poller.fetch_wu() is None


class RedisFalso:
    def __init__(self):
        self.datos = {}

    def incr(self, clave):
        self.datos[clave] = self.datos.get(clave, 0) + 1
        return self.datos[clave]

    def decr(self, clave):
        self.datos[clave] -= 1

    def expire(self, clave, segundos):
        pass


def test_las_cuotas_suman_menos_que_el_limite_de_wu():
    from app.cuota_wu import CUOTAS
    assert sum(CUOTAS.values()) <= 1450


def test_cada_proceso_cabe_en_su_parte_de_la_cuota():
    from app.cuota_wu import CUOTAS, DIA
    from app.routes.api import CACHE_MAPA_LLUVIAS_TTL, ESTACIONES_MAPA_LLUVIAS
    from scripts import historial_estaciones_poller as historial
    from scripts.backfill_historial_wu import ESTACIONES_DEFAULT
    assert DIA / wu_poller.POLL_INTERVAL <= CUOTAS["estacion"]
    assert DIA / CACHE_MAPA_LLUVIAS_TTL * len(ESTACIONES_MAPA_LLUVIAS) <= CUOTAS["mapa"]
    assert DIA / historial.POLL_INTERVAL * len(ESTACIONES_DEFAULT) <= CUOTAS["historial"]


def test_la_cuota_se_reparte_en_todo_el_dia():
    from app.cuota_wu import tomar
    redis, gastadas = RedisFalso(), 0
    madrugada = datetime(2026, 11, 26, 0, 30, tzinfo=timezone.utc)
    # Con 750 al dia a las 00:30 solo tocan 16; el resto se guarda para mas tarde.
    for _ in range(100):
        gastadas += tomar("estacion", madrugada, redis)
    assert gastadas == 16
    assert tomar("estacion", datetime(2026, 11, 26, 1, 0, tzinfo=timezone.utc), redis)


def test_al_dia_siguiente_la_cuota_vuelve_a_empezar():
    from app.cuota_wu import tomar
    redis = RedisFalso()
    noche = datetime(2026, 11, 26, 23, 59, tzinfo=timezone.utc)
    while tomar("mapa", noche, redis):
        pass
    assert tomar("mapa", datetime(2026, 11, 27, 0, 0, tzinfo=timezone.utc), redis)


def test_sin_redis_no_se_frena_la_consulta():
    from app.cuota_wu import tomar

    class Caido:
        def incr(self, clave):
            raise ConnectionError("redis caido")

    assert tomar("estacion", cliente=Caido())


def test_el_poller_no_llama_a_wu_sin_cuota(monkeypatch):
    llamadas = []
    monkeypatch.setattr(wu_poller, "tomar", lambda consumidor: False)
    monkeypatch.setattr(wu_poller.requests, "get", lambda *a, **k: llamadas.append(1))
    assert wu_poller.fetch_wu() is None and not llamadas
