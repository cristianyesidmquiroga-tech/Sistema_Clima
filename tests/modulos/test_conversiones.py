from app.models.models import (
    aplicar_compensacion_termica,
    corregir_humedad_por_temp,
    fahrenheit_a_celsius,
    inhg_a_hpa,
    mph_a_kmh,
    pulgadas_a_mm,
)


def test_fahrenheit_a_celsius():
    assert fahrenheit_a_celsius(32) == 0
    assert fahrenheit_a_celsius('82.5') == 28.1
    assert fahrenheit_a_celsius(None) is None
    assert fahrenheit_a_celsius('abc') is None


def test_mph_a_kmh():
    assert mph_a_kmh(10) == 16.1
    assert mph_a_kmh(None) is None


def test_pulgadas_a_mm():
    assert pulgadas_a_mm(1) == 25.4
    assert pulgadas_a_mm('0.57') == 14.48


def test_inhg_a_hpa():
    assert inhg_a_hpa(29.92) == 1013.2


def test_sin_sol_no_hay_compensacion():
    assert aplicar_compensacion_termica(25.0, 100, 2) == 25.0


def test_sol_fuerte_sin_viento_resta_ocho_grados():
    assert aplicar_compensacion_termica(30.0, 1300, 1) == 22.0


def test_el_viento_reduce_la_compensacion():
    sin_viento = aplicar_compensacion_termica(30.0, 1300, 1)
    con_viento = aplicar_compensacion_termica(30.0, 1300, 12)
    assert con_viento > sin_viento


def test_compensacion_con_datos_faltantes_devuelve_la_temperatura():
    assert aplicar_compensacion_termica(30.0, None, 3) == 30.0
    assert aplicar_compensacion_termica(None, 900, 3) is None


def test_la_humedad_sube_cuando_la_temperatura_baja():
    assert corregir_humedad_por_temp(40, 30, 22) > 40


def test_humedad_sin_cambio_de_temperatura():
    assert corregir_humedad_por_temp(55, 25, 25) == 55
