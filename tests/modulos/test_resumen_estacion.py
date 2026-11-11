from datetime import datetime
from types import SimpleNamespace

from app.models.resumen_estacion import resumen_semanal

CAMPOS = ('temp_max', 'temp_min', 'humedad_max', 'humedad_min', 'rafaga_max',
          'presion_max', 'presion_min', 'uv_max', 'lluvia_mm')


def fila(momento_utc, **valores):
    base = dict.fromkeys(CAMPOS)
    base.update(valores)
    return SimpleNamespace(timestamp=momento_utc, **base)


def test_sin_filas_no_hay_resumen():
    assert resumen_semanal([]) == {'disponible': False}


def test_maximo_y_minimo_con_su_dia_y_hora():
    filas = [
        fila(datetime(2026, 10, 12, 18, 0), temp_max=24.0, temp_min=20.0),
        fila(datetime(2026, 10, 13, 19, 0), temp_max=29.4, temp_min=21.0),
        fila(datetime(2026, 10, 14, 11, 0), temp_max=25.0, temp_min=14.2),
    ]
    temperatura = resumen_semanal(filas)['extremos']['temperatura']
    assert temperatura['max'] == {'valor': 29.4, 'dia': '2026-10-13', 'hora': '14:00'}
    assert temperatura['min'] == {'valor': 14.2, 'dia': '2026-10-14', 'hora': '06:00'}


def test_el_dia_se_cuenta_en_hora_de_colombia():
    filas = [fila(datetime(2026, 10, 14, 2, 0), temp_max=30.0, temp_min=18.0)]
    assert resumen_semanal(filas)['extremos']['temperatura']['max']['dia'] == '2026-10-13'


def test_en_un_empate_gana_la_primera_vez():
    filas = [
        fila(datetime(2026, 10, 12, 18, 0), temp_max=28.0),
        fila(datetime(2026, 10, 13, 18, 0), temp_max=28.0),
    ]
    assert resumen_semanal(filas)['extremos']['temperatura']['max']['dia'] == '2026-10-12'


def test_los_valores_vacios_se_ignoran():
    filas = [
        fila(datetime(2026, 10, 12, 18, 0), temp_max=None, humedad_max=None),
        fila(datetime(2026, 10, 12, 19, 0), temp_max=22.5, humedad_max=88.0),
    ]
    extremos = resumen_semanal(filas)['extremos']
    assert extremos['temperatura']['max']['valor'] == 22.5
    assert extremos['humedad']['max']['valor'] == 88.0
    assert extremos['presion']['max'] is None


def test_lluvia_suma_por_dia_y_marca_el_mas_lluvioso():
    filas = [
        fila(datetime(2026, 10, 12, 15, 0), lluvia_mm=1.0),
        fila(datetime(2026, 10, 12, 16, 0), lluvia_mm=0.5),
        fila(datetime(2026, 10, 13, 15, 0), lluvia_mm=4.0),
        fila(datetime(2026, 10, 14, 15, 0), lluvia_mm=0.0),
    ]
    resumen = resumen_semanal(filas)
    assert [d['lluvia_mm'] for d in resumen['por_dia']] == [1.5, 4.0, 0.0]
    assert resumen['extremos']['lluvia']['total'] == 5.5
    assert resumen['extremos']['lluvia']['dia_mas_lluvioso'] == {'valor': 4.0, 'dia': '2026-10-13'}


def test_semana_sin_lluvia_no_inventa_un_dia_lluvioso():
    filas = [fila(datetime(2026, 10, 12, 15, 0), lluvia_mm=0.0)]
    assert resumen_semanal(filas)['extremos']['lluvia']['dia_mas_lluvioso'] is None


def test_por_dia_va_en_orden_con_las_horas_registradas():
    filas = [
        fila(datetime(2026, 10, 13, 15, 0), temp_max=20.0, temp_min=15.0),
        fila(datetime(2026, 10, 12, 15, 0), temp_max=22.0, temp_min=16.0),
        fila(datetime(2026, 10, 12, 16, 0), temp_max=23.0, temp_min=17.0),
    ]
    resumen = resumen_semanal(filas)
    assert [d['dia'] for d in resumen['por_dia']] == ['2026-10-12', '2026-10-13']
    assert resumen['por_dia'][0]['horas'] == 2
    assert resumen['por_dia'][0]['temp_max'] == 23.0
    assert resumen['desde'] == '2026-10-12' and resumen['hasta'] == '2026-10-13'
