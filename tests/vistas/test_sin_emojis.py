import re
from pathlib import Path

APP = Path(__file__).resolve().parents[2] / 'app'
EMOJI = re.compile('[\U0001F300-\U0001FAFF\u2600-\u26FF\u2705\u274C\u2744\u2B50\uFE0F]')


def test_ninguna_pantalla_usa_emojis():
    archivos = [*APP.glob('templates/**/*.html'), *APP.glob('static/js/**/*.js')]
    con_emoji = [f'{a.relative_to(APP)}:{n}' for a in archivos
                 for n, linea in enumerate(a.read_text(encoding='utf-8').splitlines(), 1) if EMOJI.search(linea)]
    assert not con_emoji, con_emoji
