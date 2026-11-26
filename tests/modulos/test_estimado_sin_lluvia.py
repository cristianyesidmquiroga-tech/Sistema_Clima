from datetime import datetime, timedelta, timezone

from app.routes import api


def test_con_estacion_callada_el_modelo_no_marca_lluvia(app, monkeypatch):
    vieja = (datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)).isoformat() + "Z"
    monkeypatch.setattr(api, "obtener_ultima_lectura",
                        lambda: {"timestamp": vieja, "lluvia_hora": 0.4, "temp_exterior": 18.0})
    monkeypatch.setattr(api, "obtener_estimado_open_meteo", lambda: {"temp_exterior": 20.8})
    with app.app_context():
        api.cache.delete_memoized(api.armar_lectura_actual)
        datos = api.armar_lectura_actual()
    assert datos["fuente"] == "estimado"
    assert datos["temp_exterior"] == 20.8
    assert datos["lluvia_hora"] is None


def test_el_estimado_no_pide_precipitacion_al_modelo(monkeypatch):
    pedidos = []

    class Respuesta:
        def raise_for_status(self):
            pass

        def json(self):
            return {"current": {"temperature_2m": 20.8, "precipitation": 0.1}}

    def get(url, params, timeout):
        pedidos.append(params["current"])
        return Respuesta()

    monkeypatch.setattr(api.requests, "get", get)
    estimado = api.obtener_estimado_open_meteo()
    assert "precipitation" not in pedidos[0]
    assert "lluvia_hora" not in estimado
