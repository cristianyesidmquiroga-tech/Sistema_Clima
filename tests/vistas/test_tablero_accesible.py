import re
from pathlib import Path

HTML = (Path(__file__).resolve().parents[2] / 'app' / 'templates' / 'paginas' / 'index.html').read_text(encoding='utf-8')


def test_se_puede_hacer_zoom_en_el_celular():
    assert 'user-scalable=no' not in HTML and 'maximum-scale' not in HTML


def test_hay_un_solo_titulo_principal():
    assert len(re.findall(r'<h1\b', HTML)) == 1


def test_tiene_descripcion_para_buscadores():
    assert '<meta name="description"' in HTML


def test_textos_en_espanol_de_colombia():
    for voseo in ('alejás', 'Tocá', 'tocá', 'mirá', 'hacé'):
        assert voseo not in HTML
