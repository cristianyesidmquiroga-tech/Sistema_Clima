from datetime import datetime, timezone

from scripts.publicar_reporte_velez import segundos_para_publicar

SEMANA = 7 * 24 * 3600
AHORA = datetime(2026, 11, 25, 15, 0, tzinfo=timezone.utc)


def test_sin_reportes_publica_de_una():
    assert segundos_para_publicar(None, AHORA, SEMANA) == 0


def test_un_reinicio_a_los_dos_dias_no_publica_otro():
    ultimo = {"fecha_publicacion": "2026-11-23T15:00:00Z"}
    assert segundos_para_publicar(ultimo, AHORA, SEMANA) == 5 * 24 * 3600


def test_pasada_la_semana_publica():
    ultimo = {"fecha_publicacion": "2026-11-17T15:00:00Z"}
    assert segundos_para_publicar(ultimo, AHORA, SEMANA) == 0
