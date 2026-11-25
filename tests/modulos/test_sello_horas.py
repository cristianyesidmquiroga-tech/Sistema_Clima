from datetime import datetime
from types import SimpleNamespace

import pytest

from app.models.sellos import CAMPOS_SELLADOS, texto_de_hora
from scripts import sellador_horas as s

SAL = "x" * 32
CFG = {"SELLADOR_URL": "https://sellador.test/", "SELLADOR_SECRETO": "secreto", "SELLO_SAL": SAL}


def _lectura(id_, minuto, temp):
    campos = dict.fromkeys(CAMPOS_SELLADOS)
    campos["temp_exterior"] = temp
    return SimpleNamespace(id=id_, timestamp=datetime(2026, 11, 25, 14, minuto), **campos)


class Respuesta:
    def __init__(self, codigo, datos=None):
        self.status_code, self._datos, self.text = codigo, datos, ""

    def json(self):
        return self._datos


def test_huella_es_keccak256_de_sal_mas_datos():
    # keccak256 de 32 ceros, valor conocido de Ethereum
    assert s.huella("", "\x00" * 32) == "0x290decd9548b62a8d60345a988386fc84ba6bc95484008f6362f93160ef3e563"


def test_huella_no_depende_del_orden_y_cambia_con_un_dato():
    a, b = _lectura(1, 0, 21.5), _lectura(2, 2, 21.7)
    h = s.huella(texto_de_hora([a, b]), SAL)
    assert h == s.huella(texto_de_hora([b, a]), SAL)
    assert h != s.huella(texto_de_hora([a, _lectura(2, 2, 21.8)]), SAL)


def test_sal_corta_se_rechaza():
    with pytest.raises(ValueError):
        s.huella("datos", "corta")


def test_solo_horas_cerradas_con_margen():
    horas = s.horas_pendientes(datetime(2026, 11, 25, 15, 5), horas_atras=3)
    assert horas == [datetime(2026, 11, 25, h) for h in (11, 12, 13)]
    assert s.horas_pendientes(datetime(2026, 11, 25, 15, 15), horas_atras=1) == [datetime(2026, 11, 25, 14)]


def test_manda_app_huella_y_secreto_al_sellador():
    llamadas = []

    def post(url, json, headers, timeout):
        llamadas.append((url, json, headers))
        return Respuesta(200, {"tx": "0xabc", "yaSellada": False})

    s.sellar("https://sellador.test/", "secreto", "0x01", post)
    assert llamadas == [("https://sellador.test/api/sellar", {"app": "clima", "huella": "0x01"},
                         {"Authorization": "Bearer secreto"})]


def test_nodo_caido_y_rechazo_se_distinguen():
    with pytest.raises(s.SelladorCaido):
        s.sellar("u", "k", "0x01", lambda *a, **k: Respuesta(503))
    with pytest.raises(RuntimeError):
        s.sellar("u", "k", "0x01", lambda *a, **k: Respuesta(401))


def test_sella_horas_con_datos_y_no_repite_las_confirmadas():
    horas = [datetime(2026, 11, 25, h) for h in (12, 13, 14)]
    datos = {horas[0]: [_lectura(1, 0, 20.0)], horas[2]: [_lectura(3, 0, 22.0)]}
    enviadas = []

    def post(url, json, headers, timeout):
        enviadas.append(json["huella"])
        return Respuesta(200, {"tx": None, "yaSellada": len(enviadas) == 1})

    ya = set()
    n = s.sellar_pendientes(CFG, horas, lambda h: datos.get(h, []), texto_de_hora, ya, post)
    assert len(enviadas) == 2 and n == 1
    assert s.sellar_pendientes(CFG, horas, lambda h: datos.get(h, []), texto_de_hora, ya, post) == 0
    assert len(enviadas) == 2


def test_sin_configuracion_avisa_que_falta(monkeypatch):
    for n in ("SELLADOR_URL", "SELLADOR_SECRETO", "SELLO_SAL"):
        monkeypatch.delenv(n, raising=False)
    _, faltan = s.config()
    assert faltan == ["SELLADOR_URL", "SELLADOR_SECRETO", "SELLO_SAL"]
