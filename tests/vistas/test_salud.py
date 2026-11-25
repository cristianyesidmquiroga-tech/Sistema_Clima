from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]


def test_salud_responde_con_la_base(client):
    r = client.get('/salud')
    assert r.status_code == 200
    assert r.get_json() == {'estado': 'ok', 'db': True}


def test_salud_avisa_si_la_base_no_responde(client, monkeypatch):
    monkeypatch.setattr('app.routes.api.base_responde', lambda: False)
    r = client.get('/salud')
    assert r.status_code == 200
    assert r.get_json() == {'estado': 'ok', 'db': False}


def test_salud_sigue_en_modo_mantenimiento(client, monkeypatch):
    monkeypatch.setenv('MODO_MANTENIMIENTO', 'true')
    assert client.get('/salud').status_code == 200
    assert client.get('/').status_code == 503


def test_el_contenedor_web_tiene_healthcheck():
    texto = (RAIZ / 'docker-compose.yml').read_text(encoding='utf-8')
    bloque = texto.split('\n  app:', 1)[1].split('\n  poller:', 1)[0]
    assert 'healthcheck:' in bloque
    assert '127.0.0.1:8080/salud' in bloque
