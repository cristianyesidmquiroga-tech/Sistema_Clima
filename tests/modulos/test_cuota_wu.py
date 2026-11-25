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


def test_poller_y_mapa_caben_en_la_cuota_diaria():
    from app.routes.api import CACHE_MAPA_LLUVIAS_TTL, ESTACIONES_MAPA_LLUVIAS
    dia = 24 * 3600
    consultas = dia / wu_poller.POLL_INTERVAL + dia / CACHE_MAPA_LLUVIAS_TTL * len(ESTACIONES_MAPA_LLUVIAS)
    assert consultas < 1500
