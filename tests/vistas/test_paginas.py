import pytest

PAGINAS = ['/', '/mapa-estaciones', '/reporte-velez', '/privacidad', '/nosotros']

APIS = [
    '/api/historial', '/api/stats', '/api/stats/comparative', '/api/mapa_lluvias',
    '/api/reporte_velez', '/api/analisis?tipo=dias', '/api/analisis?tipo=semanas',
    '/api/analisis/semana', '/api/noticias', '/api/estacion/IGUAVA3/historial',
]


@pytest.mark.parametrize('ruta', PAGINAS)
def test_las_paginas_cargan(client, ruta):
    assert client.get(ruta).status_code == 200


@pytest.mark.parametrize('ruta', APIS)
def test_las_apis_responden_sin_datos(client, ruta):
    r = client.get(ruta)
    assert r.status_code == 200
    assert r.get_json() is not None


def test_ruta_inexistente_muestra_la_pagina_404(client):
    r = client.get('/no-existe')
    assert r.status_code == 404
    assert '<html' in r.get_data(as_text=True)


def test_estacion_desconocida_responde_404(client):
    assert client.get('/api/estacion/NOEXISTE/historial').status_code == 404


def test_analisis_con_tipo_invalido_responde_400(client):
    assert client.get('/api/analisis?tipo=siglos').status_code == 400


def test_fecha_sin_parametro_responde_400(client):
    assert client.get('/api/fecha').status_code == 400


def test_fecha_con_formato_invalido_responde_400(client):
    assert client.get('/api/fecha?fecha=ayer').status_code == 400


def test_endpoint_de_prueba_esta_deshabilitado(client):
    assert client.get('/api/test').status_code == 404


def test_cabeceras_de_seguridad(client):
    h = client.get('/').headers
    assert 'max-age' in h['Strict-Transport-Security']
    assert 'camera=()' in h['Permissions-Policy']
    assert h['X-Frame-Options'] == 'DENY'
    csp = h['Content-Security-Policy']
    assert "font-src 'self' data:" in csp
    assert 'rainviewer' not in csp


def test_exportar_devuelve_un_excel(client):
    r = client.get('/api/exportar?dias=1')
    assert r.status_code == 200
    assert r.data[:2] == b'PK'
