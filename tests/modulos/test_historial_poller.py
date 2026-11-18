from datetime import date

from scripts.historial_estaciones_poller import fechas_a_completar


def test_hoy_siempre_y_viejos_solo_si_faltan():
    hoy = date(2026, 11, 18)
    guardados = {date(2026, 11, 16), date(2026, 11, 14)}
    fechas = fechas_a_completar(hoy, 8, lambda f: f in guardados)
    assert hoy in fechas
    assert date(2026, 11, 16) not in fechas
    assert date(2026, 11, 17) in fechas
    assert date(2026, 11, 11) in fechas
    assert date(2026, 11, 10) not in fechas


def test_tabla_vacia_trae_toda_la_ventana():
    fechas = fechas_a_completar(date(2026, 11, 18), 8, lambda f: False)
    assert len(fechas) == 8
