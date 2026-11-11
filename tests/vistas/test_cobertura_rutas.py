import pytest

VISTAS_CONSTRUCCION = ['/rios', '/cultivos', '/incendios', '/riesgo-geologico']


def test_reporte_velez_pdf_sin_reporte_responde_404(client):
    assert client.get('/api/reporte_velez/pdf').status_code == 404


def test_fecha_valida_responde_200(client):
    r = client.get('/api/fecha?fecha=2026-01-01')
    assert r.status_code == 200
    assert r.get_json() is not None


@pytest.mark.parametrize('ruta', VISTAS_CONSTRUCCION)
def test_vistas_en_construccion_cargan(client, ruta):
    assert client.get(ruta).status_code == 200


def test_modo_mantenimiento_corta_las_paginas(client, monkeypatch):
    monkeypatch.setenv('MODO_MANTENIMIENTO', 'true')
    assert client.get('/').status_code == 503
    assert client.get('/static/js/dashboard/core.js').status_code != 503


def test_redireccion_canonica_apex_a_www(client):
    r = client.get('/reporte-velez', base_url='http://nuestroclima.co')
    assert r.status_code == 301
    assert r.headers['Location'].startswith('https://www.nuestroclima.co/reporte-velez')


def test_localhost_no_redirige(client):
    assert client.get('/', base_url='http://localhost').status_code == 200
