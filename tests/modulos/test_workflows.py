import re
from pathlib import Path

FLUJOS = sorted((Path(__file__).resolve().parents[2] / '.github' / 'workflows').glob('*.yml'))


def test_hay_workflows():
    assert FLUJOS


def test_solo_corren_en_pull_request_o_programados():
    for flujo in FLUJOS:
        texto = flujo.read_text(encoding='utf-8')
        disparadores = texto.split('\non:\n', 1)[1].split('\n\n', 1)[0]
        assert 'push:' not in disparadores and 'pull_request_target' not in disparadores, flujo.name
        assert 'pull_request:' in disparadores, flujo.name


def test_concurrencia_permisos_y_tiempo_limite():
    for flujo in FLUJOS:
        texto = flujo.read_text(encoding='utf-8')
        assert 'cancel-in-progress: true' in texto, flujo.name
        assert '\npermissions:\n  contents: read' in texto, flujo.name
        assert 'timeout-minutes:' in texto, flujo.name


def test_actions_fijadas_por_sha():
    for flujo in FLUJOS:
        for uso in re.findall(r'uses:\s*(\S+)', flujo.read_text(encoding='utf-8')):
            assert re.search(r'@[0-9a-f]{40}$', uso), f'{flujo.name}: {uso}'
