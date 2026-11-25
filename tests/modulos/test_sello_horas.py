from datetime import datetime
from types import SimpleNamespace

import pytest

from app.models.sellos import CAMPOS_SELLADOS, texto_de_hora
from scripts import sellador_horas as s

SAL = "x" * 32


def _lectura(id_, minuto, temp):
    campos = dict.fromkeys(CAMPOS_SELLADOS)
    campos["temp_exterior"] = temp
    return SimpleNamespace(id=id_, timestamp=datetime(2026, 11, 25, 14, minuto), **campos)


def test_huella_no_depende_del_orden_y_cambia_si_cambia_un_dato():
    a, b = _lectura(1, 0, 21.5), _lectura(2, 2, 21.7)
    h = s.huella(texto_de_hora([a, b]), SAL)
    assert h == s.huella(texto_de_hora([b, a]), SAL)
    assert h != s.huella(texto_de_hora([a, _lectura(2, 2, 21.8)]), SAL)
    assert h != s.huella(texto_de_hora([a, b]), "y" * 32)


def test_sal_corta_se_rechaza():
    with pytest.raises(ValueError):
        s.huella("datos", "corta")


def test_solo_horas_cerradas_con_margen():
    horas = s.horas_pendientes(datetime(2026, 11, 25, 15, 5), horas_atras=3)
    assert horas == [datetime(2026, 11, 25, h) for h in (11, 12, 13)]
    assert s.horas_pendientes(datetime(2026, 11, 25, 15, 15), horas_atras=1) == [datetime(2026, 11, 25, 14)]


class RegistroFalso:
    def __init__(self, ya):
        self.ya, self.selladas = set(ya), []

    def sellada(self, h):
        return h in self.ya

    def sellar(self, h):
        self.selladas.append(h)
        self.ya.add(h)


def test_sella_solo_horas_con_datos_y_sin_sello_previo():
    horas = [datetime(2026, 11, 25, h) for h in (12, 13, 14)]
    datos = {horas[0]: [_lectura(1, 0, 20.0)], horas[2]: [_lectura(3, 0, 22.0)]}
    ya = s.huella(texto_de_hora(datos[horas[0]]), SAL)
    registro = RegistroFalso([ya])
    n = s.sellar_pendientes(registro, SAL, horas, lambda h: datos.get(h, []), texto_de_hora)
    assert n == 1 and registro.selladas == [s.huella(texto_de_hora(datos[horas[2]]), SAL)]
    assert s.sellar_pendientes(registro, SAL, horas, lambda h: datos.get(h, []), texto_de_hora) == 0


def test_sin_configuracion_avisa_que_falta(monkeypatch):
    for n in ("SNA_RPC_URL", "SNA_RPC_CLAVE", "SELLO_SAL"):
        monkeypatch.delenv(n, raising=False)
    _, faltan = s.config()
    assert "SNA_RPC_CLAVE" in faltan and "SELLO_SAL" in faltan
