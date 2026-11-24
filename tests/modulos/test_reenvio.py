import requests

from app import reenvio


class HiloInmediato:
    def __init__(self, target, args, daemon):
        self.target, self.args = target, args

    def start(self):
        self.target(*self.args)


def test_sin_variables_no_reenvia(monkeypatch):
    monkeypatch.delenv('PILOTO_INGESTA_URL', raising=False)
    monkeypatch.delenv('PILOTO_PASSKEY', raising=False)
    llamadas = []
    monkeypatch.setattr(reenvio.requests, 'post', lambda *a, **k: llamadas.append(a))
    assert reenvio.reenviar_al_piloto({'tempf': '70'}) is False
    assert llamadas == []


def test_reenvia_con_la_clave_del_piloto(monkeypatch):
    monkeypatch.setenv('PILOTO_INGESTA_URL', 'https://piloto.test/data/report/')
    monkeypatch.setenv('PILOTO_PASSKEY', 'clave-piloto')
    monkeypatch.setattr(reenvio.threading, 'Thread', HiloInmediato)
    enviado = {}

    def falso_post(url, data, timeout):
        enviado.update(url=url, data=data, timeout=timeout)

    monkeypatch.setattr(reenvio.requests, 'post', falso_post)
    original = {'PASSKEY': 'clave-produccion', 'tempf': '70'}

    assert reenvio.reenviar_al_piloto(original) is True
    assert enviado['url'] == 'https://piloto.test/data/report/'
    assert enviado['data'] == {'PASSKEY': 'clave-piloto', 'tempf': '70'}
    assert original['PASSKEY'] == 'clave-produccion'


def test_un_error_del_piloto_no_rompe(monkeypatch):
    monkeypatch.setenv('PILOTO_INGESTA_URL', 'https://piloto.test/data/report/')
    monkeypatch.setenv('PILOTO_PASSKEY', 'clave-piloto')
    monkeypatch.setattr(reenvio.threading, 'Thread', HiloInmediato)

    def falla(*a, **k):
        raise requests.ConnectionError('caido')

    monkeypatch.setattr(reenvio.requests, 'post', falla)
    assert reenvio.reenviar_al_piloto({'tempf': '70'}) is True
