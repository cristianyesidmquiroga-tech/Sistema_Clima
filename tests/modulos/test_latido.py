import importlib
import os
import re
from pathlib import Path

import pytest

from scripts import latido

RAIZ = Path(__file__).resolve().parents[2]
PROCESOS = ["wu_poller", "historial_estaciones_poller", "lecturas_fews_poller",
            "publicar_reporte_velez", "capturas_mapas_poller", "email_reporter", "sellador_horas"]


def test_latir_crea_el_archivo_y_queda_sano(tmp_path):
    ruta = str(tmp_path / "latido")
    assert not latido.sano(60, ruta)
    latido.latir(ruta)
    assert latido.sano(60, ruta)


def test_un_latido_viejo_no_esta_sano(tmp_path):
    ruta = str(tmp_path / "latido")
    latido.latir(ruta)
    viejo = os.path.getmtime(ruta) - 3600
    os.utime(ruta, (viejo, viejo))
    assert not latido.sano(1800, ruta)


def test_dormir_late_en_cada_tramo(tmp_path):
    ruta = str(tmp_path / "latido")
    tramos = []
    latido.dormir(150, ruta, paso=60, esperar=tramos.append)
    assert tramos == [60, 60, 30]
    assert latido.sano(5, ruta)


@pytest.mark.parametrize("nombre", PROCESOS)
def test_cada_proceso_espera_con_latido(nombre):
    modulo = importlib.import_module(f"scripts.{nombre}")
    assert modulo.dormir is latido.dormir
    assert "time.sleep(" not in (RAIZ / "scripts" / f"{nombre}.py").read_text(encoding="utf-8")


def test_todos_los_servicios_tienen_healthcheck():
    texto = (RAIZ / "docker" / "docker-compose.yml").read_text(encoding="utf-8")
    servicios = texto.split("services:\n", 1)[1].split("\nvolumes:\n", 1)[0]
    bloques = re.split(r"\n(?=  [a-z_]+:\n)", "\n" + servicios)
    nombres = {b.split(":", 1)[0].strip(): b for b in bloques if b.strip()}
    assert len(nombres) == 10
    assert [n for n, b in nombres.items() if "    healthcheck:" not in b] == []
