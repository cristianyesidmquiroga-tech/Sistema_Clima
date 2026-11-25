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
    texto = (RAIZ / 'docker' / 'docker-compose.yml').read_text(encoding='utf-8')
    bloque = texto.split('\n  app:', 1)[1].split('\n  poller:', 1)[0]
    entorno = bloque.split('environment:', 1)[1].split('\n    expose:', 1)[0]
    return set(re.findall(r'^\s+([A-Z_]+):', entorno, re.M))


def test_toda_variable_que_lee_la_app_llega_al_contenedor():
    faltan = _variables_de_la_app() - _entorno_del_servicio_app()
    assert not faltan, f'Faltan en docker/docker-compose.yml (servicio app): {sorted(faltan)}'


def test_ningun_servicio_publica_puertos_en_el_servidor():
    # Coolify llega por la red interna; un puerto publicado salta Traefik y su HTTPS.
    texto = (RAIZ / 'docker' / 'docker-compose.yml').read_text(encoding='utf-8')
    assert '\n    ports:' not in texto


def test_cada_build_apunta_al_dockerfile_de_docker():
    texto = (RAIZ / 'docker' / 'docker-compose.yml').read_text(encoding='utf-8')
    assert texto.count('dockerfile: docker/Dockerfile') == texto.count('    build:')
    assert (RAIZ / 'docker' / 'Dockerfile').exists()
    assert (RAIZ / 'docker' / 'Dockerfile.dockerignore').exists()


def test_dependencias_en_requisitos_y_raiz_sin_sueltos():
    assert (RAIZ / 'requisitos' / 'requirements.txt').exists()
    assert 'COPY requisitos/requirements.txt' in (RAIZ / 'docker' / 'Dockerfile').read_text(encoding='utf-8')
    sueltos = {'requirements.txt', 'requirements-dev.txt', 'Dockerfile', 'docker-compose.yml', '.env.example'}
    assert not [n for n in sueltos if (RAIZ / n).exists()]


def test_cada_servicio_rota_sus_logs():
    texto = (RAIZ / 'docker' / 'docker-compose.yml').read_text(encoding='utf-8')
    servicios = re.findall(r'^  ([a-z_]+):\n    (?:image|build)', texto, re.M)
    assert len(servicios) == texto.count('    logging: *logs') == 10
    assert 'max-size: "10m"' in texto


def test_los_secretos_son_obligatorios_y_no_caen_en_vacio():
    texto = (RAIZ / 'docker' / 'docker-compose.yml').read_text(encoding='utf-8')
    for secreto in ('DB_USER', 'DB_PASS', 'STATION_PASSKEY'):
        assert f'${{{secreto}}}' not in texto and f'${{{secreto}:-}}' not in texto, secreto
        assert f'${{{secreto}:?}}' in texto, secreto
