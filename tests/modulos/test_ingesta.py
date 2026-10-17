from app.models.models import Lectura

DATOS = {
    'tempf': '70', 'tempinf': '71', 'humidity': '60', 'humidityin': '50',
    'windspeedmph': '2', 'windgustmph': '5', 'winddir': '90',
    'rainratein': '0', 'dailyrainin': '0.1', 'eventrainin': '0',
    'baromrelin': '29.9', 'baromabsin': '28', 'uv': '3',
    'solarradiation': '400', 'dewptf': '55', 'feelslikef': '69',
}


def test_sin_datos_responde_400(client):
    assert client.post('/data/report/').status_code == 400


def test_passkey_incorrecta_se_rechaza(client, sesion):
    r = client.post('/data/report/', data={**DATOS, 'PASSKEY': 'otra'})
    assert r.status_code == 403
    assert Lectura.query.count() == 0


def test_sin_passkey_se_rechaza(client):
    assert client.post('/data/report/', data=DATOS).status_code == 403


def test_datos_validos_se_guardan(client, sesion):
    r = client.post('/data/report/', data={**DATOS, 'PASSKEY': 'clave-de-pruebas'})
    assert r.status_code == 200
    lectura = Lectura.query.one()
    assert lectura.temp_exterior is not None
    assert lectura.rafaga_viento == 8.0


def test_actual_sin_datos_responde_404(client):
    assert client.get('/api/actual').status_code == 404


def test_actual_no_expone_la_passkey(client):
    client.post('/data/report/', data={**DATOS, 'PASSKEY': 'clave-de-pruebas'})
    cuerpo = client.get('/api/actual').get_json()
    assert 'passkey' not in cuerpo
    assert 'clave-de-pruebas' not in client.get('/api/historial?horas=1').get_data(as_text=True)


def test_la_passkey_no_se_guarda_en_la_base(client, sesion):
    client.post('/data/report/', data={**DATOS, 'PASSKEY': 'clave-de-pruebas'})
    assert Lectura.query.one().passkey != 'clave-de-pruebas'
