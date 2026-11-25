import re
from pathlib import Path

from app.routes.api import VISTAS_EN_CONSTRUCCION

INICIO = Path(__file__).resolve().parents[2] / 'app' / 'templates' / 'paginas' / 'inicio.html'


def test_inicio_no_anuncia_como_listas_las_vistas_en_construccion():
    html = INICIO.read_text(encoding='utf-8')
    for slug in VISTAS_EN_CONSTRUCCION:
        enlace = re.search(rf'<a href="/{slug}">([^<]*)</a>', html)
        assert enlace and enlace.group(1) == 'Próximamente', slug
    assert 'tiempo real sobre la provincia' not in html
