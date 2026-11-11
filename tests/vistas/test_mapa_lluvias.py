import app.routes.api as api_mod


def _obs_falsa(station_id):
    if station_id in ('IGUAVA3', 'IBARBO1'):
        return {
            'lat': 5.9, 'lon': -73.7, 'humidity': 50,
            'obsTimeLocal': '2026-11-11 10:00:00',
            'metric': {'precipTotal': 0, 'precipRate': 0, 'temp': 27, 'windSpeed': 3},
        }
    return None


def test_todas_las_estaciones_aparecen_aunque_no_reporten(client, monkeypatch):
    monkeypatch.setattr(api_mod, 'WU_API_KEY', 'clave-de-pruebas')
    monkeypatch.setattr(api_mod, '_consultar_estacion_wu', _obs_falsa)

    datos = client.get('/api/mapa_lluvias').get_json()
    ids = {d['id'] for d in datos}
    assert ids == {e['id'] for e in api_mod.ESTACIONES_MAPA_LLUVIAS}

    caida = next(d for d in datos if d['id'] == 'IBARBO2')
    assert caida['nivel'] == 'sin_dato'
    assert caida['lat'] is not None and caida['lon'] is not None
    assert caida['temp'] is None and caida['lluvia_mm'] is None

    viva = next(d for d in datos if d['id'] == 'IGUAVA3')
    assert viva['temp'] == 27
    assert viva['nivel'] == 'sin_lluvia'
