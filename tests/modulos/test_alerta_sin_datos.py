from scripts import latido, wu_poller


def _estado():
    return {"ultimo_ok": 0, "avisado": False}


def test_avisa_una_sola_vez_cuando_pasan_30_minutos_sin_datos():
    correos = []
    estado = _estado()
    for minuto in (10, 29, 30, 45, 90):
        wu_poller.revisar_frescura(estado, False, minuto * 60, lambda a, c: correos.append(a))
    assert len(correos) == 1
    assert 'no envia datos' in correos[0]


def test_avisa_cuando_los_datos_vuelven():
    correos = []
    estado = _estado()
    wu_poller.revisar_frescura(estado, False, 3600, lambda a, c: correos.append(a))
    wu_poller.revisar_frescura(estado, True, 3700, lambda a, c: correos.append(a))
    assert len(correos) == 2 and 'volvieron' in correos[1]
    assert estado == {"ultimo_ok": 3700, "avisado": False}


def test_con_datos_al_dia_no_avisa():
    correos = []
    estado = _estado()
    for minuto in range(0, 120, 5):
        wu_poller.revisar_frescura(estado, True, minuto * 60, lambda a, c: correos.append(a))
    assert correos == []


def test_dormir_sin_latir_no_toca_el_archivo(tmp_path):
    ruta = str(tmp_path / "latido")
    latido.dormir(120, ruta, esperar=lambda s: None, latiendo=False)
    assert not latido.sano(60, ruta)
