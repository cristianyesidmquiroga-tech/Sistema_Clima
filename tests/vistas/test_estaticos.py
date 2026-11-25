import re

import pytest

from app import estaticos

VERSION = re.compile(r'/static/css/dashboard/base\.css\?v=([0-9a-f]{10})"')


@pytest.fixture
def web(app):
    return app.test_client()


def test_la_pagina_pide_los_estaticos_con_version_de_contenido(web):
    html = web.get('/').get_data(as_text=True)
    assert VERSION.search(html)
    assert '?v=1"' not in html and '?v=2"' not in html


def test_estatico_con_version_se_guarda_un_anio(web):
    r = web.get('/static/css/dashboard/base.css?v=abc123')
    assert r.status_code == 200
    assert r.headers['Cache-Control'] == 'public, max-age=31536000, immutable'


def test_estatico_sin_version_se_guarda_una_hora(web):
    r = web.get('/static/img/mapa-estaciones/icon-sun.svg')
    assert r.headers['Cache-Control'] == 'public, max-age=3600'


def test_la_pagina_no_queda_guardada_como_inmutable(web):
    assert 'immutable' not in web.get('/').headers.get('Cache-Control', '')


def test_la_version_cambia_si_cambia_el_archivo(tmp_path):
    archivo = tmp_path / 'x.css'
    archivo.write_text('a{}')
    antes = estaticos._huella(str(archivo), 1)
    archivo.write_text('b{}')
    assert estaticos._huella(str(archivo), 2) != antes
