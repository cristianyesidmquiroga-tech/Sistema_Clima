import app.security as sec


def test_ip_privada_o_invalida_es_de_confianza():
    assert sec._es_ip_privada('127.0.0.1') is True
    assert sec._es_ip_privada('192.168.1.10') is True
    assert sec._es_ip_privada('8.8.8.8') is False
    assert sec._es_ip_privada('no-es-ip') is True


def test_limite_mas_estricto_fuera_de_colombia(monkeypatch):
    monkeypatch.setattr(sec, 'obtener_pais', lambda ip: 'US')
    assert sec.limite_dinamico_por_pais('8.8.8.8') == sec.LIMITE_HORA_EXTRANJERO


def test_limite_normal_para_colombia_y_local(monkeypatch):
    monkeypatch.setattr(sec, 'obtener_pais', lambda ip: 'CO')
    assert sec.limite_dinamico_por_pais('1.2.3.4') == sec.LIMITE_HORA_COLOMBIA
    monkeypatch.setattr(sec, 'obtener_pais', lambda ip: 'LOCAL')
    assert sec.limite_dinamico_por_pais('10.0.0.1') == sec.LIMITE_HORA_COLOMBIA


def test_ip_privada_no_consulta_el_servicio_externo(monkeypatch):
    def no_llamar(*a, **k):
        raise AssertionError('no debe consultar la red para una IP privada')
    monkeypatch.setattr(sec.requests, 'get', no_llamar)
    assert sec.obtener_pais('192.168.0.1') == 'LOCAL'


def test_el_pais_se_cachea_por_ip(monkeypatch):
    sec._CACHE_PAIS.clear()
    llamadas = {'n': 0}

    class Respuesta:
        status_code = 200

        def json(self):
            return {'countryCode': 'CO'}

    def fake_get(*a, **k):
        llamadas['n'] += 1
        return Respuesta()

    monkeypatch.setattr(sec.requests, 'get', fake_get)
    assert sec.obtener_pais('200.1.2.3') == 'CO'
    assert sec.obtener_pais('200.1.2.3') == 'CO'
    assert llamadas['n'] == 1
