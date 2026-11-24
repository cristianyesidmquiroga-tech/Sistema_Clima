import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
LECTURA = re.compile(r"os\.(?:environ\.get|getenv|environ\[)\(?['\"]([A-Z_]+)['\"]")


def _variables_de_la_app():
    nombres = set()
    for archivo in (RAIZ / 'app').rglob('*.py'):
        nombres |= set(LECTURA.findall(archivo.read_text(encoding='utf-8')))
    return nombres


def _entorno_del_servicio_app():
    texto = (RAIZ / 'docker-compose.yml').read_text(encoding='utf-8')
    bloque = texto.split('\n  app:', 1)[1].split('\n  poller:', 1)[0]
    entorno = bloque.split('environment:', 1)[1].split('\n    expose:', 1)[0]
    return set(re.findall(r'^\s+([A-Z_]+):', entorno, re.M))


def test_toda_variable_que_lee_la_app_llega_al_contenedor():
    faltan = _variables_de_la_app() - _entorno_del_servicio_app()
    assert not faltan, f'Faltan en docker-compose.yml (servicio app): {sorted(faltan)}'
