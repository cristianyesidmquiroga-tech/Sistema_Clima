import pytest

from scripts import capturas_mapas_poller as capturas


def _preparar(tmp_path, monkeypatch, marcar):
    png = tmp_path / 'img' / 'vieja.png'
    png.parent.mkdir()
    png.write_bytes(b'png')
    monkeypatch.setattr(capturas, 'DIR_BASE', str(tmp_path))
    monkeypatch.setattr(capturas, 'DIR_ARCHIVO_COMPRIMIDO', str(tmp_path / 'zip'))
    monkeypatch.setattr(capturas, 'CAPAS_SATELITE', {'geocolor': {}})
    monkeypatch.setattr(capturas, 'obtener_capturas_pendientes_de_comprimir', lambda *a: [
        {'fecha_captura': '2026-07-01', 'ruta_archivo': '/img/vieja.png'}])
    monkeypatch.setattr(capturas, 'marcar_capturas_comprimidas', marcar)
    return png


def test_si_marcar_falla_el_png_no_se_borra(tmp_path, monkeypatch):
    def falla(*a):
        raise RuntimeError('base caida')
    png = _preparar(tmp_path, monkeypatch, falla)
    with pytest.raises(RuntimeError):
        capturas.comprimir_capturas_viejas()
    assert png.exists()


def test_si_marcar_funciona_el_png_queda_solo_en_el_zip(tmp_path, monkeypatch):
    marcadas = []
    png = _preparar(tmp_path, monkeypatch, lambda *a: marcadas.append(a))
    capturas.comprimir_capturas_viejas()
    assert not png.exists()
    assert marcadas and (tmp_path / 'zip' / 'geocolor_2026-07.zip').exists()
