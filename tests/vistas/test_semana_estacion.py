from datetime import datetime, timedelta

from app.models.models import HistorialEstacion, db


def sembrar(station_id, horas=30):
    ahora = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    for h in range(horas):
        db.session.add(HistorialEstacion(
            station_id=station_id, timestamp=ahora - timedelta(hours=h),
            temp_max=20 + h * 0.1, temp_min=15 - h * 0.1, lluvia_mm=0.2))
    db.session.commit()


def test_semana_sin_datos_no_esta_disponible(client):
    assert client.get('/api/estacion/IGUAVA3/semana').get_json() == {'disponible': False}


def test_semana_de_estacion_desconocida_responde_404(client):
    assert client.get('/api/estacion/NOEXISTE/semana').status_code == 404


def test_semana_con_datos_trae_extremos_y_dias(client, sesion):
    sembrar('IGUAVA3')
    cuerpo = client.get('/api/estacion/IGUAVA3/semana').get_json()
    assert cuerpo['disponible'] is True
    assert cuerpo['extremos']['temperatura']['max']['valor'] == 22.9
    assert cuerpo['extremos']['temperatura']['min']['valor'] == 12.1
    assert cuerpo['extremos']['temperatura']['max']['dia']
    assert len(cuerpo['por_dia']) >= 2
    assert cuerpo['extremos']['lluvia']['total'] == 6.0


def test_semana_solo_cuenta_la_estacion_pedida(client, sesion):
    sembrar('IGUAVA3')
    assert client.get('/api/estacion/IBARBO1/semana').get_json() == {'disponible': False}


def test_el_modal_trae_el_bloque_de_la_semana(client):
    html = client.get('/mapa-estaciones').get_data(as_text=True)
    assert 'gwStWeekExtremos' in html
    assert 'station-week.js' in html
