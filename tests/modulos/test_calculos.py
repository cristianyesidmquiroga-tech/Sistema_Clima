from datetime import datetime

from app.models.models import absoluta_a_relativa
from app.routes.api import get_moon_phase


def test_fase_lunar_en_rango_cada_mes():
    for mes in range(1, 13):
        fase = get_moon_phase(datetime(2026, mes, 15))
        assert isinstance(fase, int)
        assert 0 <= fase <= 7


def test_presion_relativa_mayor_que_absoluta_en_altura():
    assert absoluta_a_relativa(None) is None
    assert absoluta_a_relativa(800) > 800
