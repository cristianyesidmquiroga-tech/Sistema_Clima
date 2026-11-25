import json
import re

DATOS = {
    'tempf': '70', 'tempinf': '71', 'humidity': '60', 'humidityin': '50',
    'windspeedmph': '2', 'windgustmph': '5', 'winddir': '90',
    'rainratein': '0', 'dailyrainin': '0.1', 'eventrainin': '0',
    'baromrelin': '29.9', 'baromabsin': '28', 'uv': '3',
    'solarradiation': '400', 'dewptf': '55', 'feelslikef': '69',
}

BLOQUE = re.compile(r'<script type="application/json" id="lecturaInicial">(.*?)</script>', re.S)


def _enviar(client, **cambios):
    return client.post('/data/report/', data={**DATOS, **cambios, 'PASSKEY': 'clave-de-pruebas'})


def test_la_pagina_trae_la_lectura_dentro_del_html(client):
    _enviar(client)
    html = client.get('/').get_data(as_text=True)
    datos = json.loads(BLOQUE.search(html).group(1))
    assert datos['temp_exterior'] == client.get('/api/actual').get_json()['temp_exterior']
    assert 'passkey' not in datos and 'clave-de-pruebas' not in html


def test_sin_lecturas_la_pagina_carga_igual(client):
    r = client.get('/')
    assert r.status_code == 200
    assert 'id="lecturaInicial"' not in r.get_data(as_text=True)


def test_una_lectura_nueva_se_ve_sin_esperar_el_cache(client):
    _enviar(client, tempf='68')
    antes = client.get('/api/actual').get_json()['temp_exterior']
    _enviar(client, tempf='86')
    assert client.get('/api/actual').get_json()['temp_exterior'] != antes
