from flask import Flask, request
from werkzeug.middleware.proxy_fix import ProxyFix

from app import security as sec
from app.cloudflare import IPDesdeCloudflare, es_cloudflare


def _cliente():
    app = Flask(__name__)

    @app.get('/')
    def ver():
        return {'ip': request.remote_addr, 'pais': request.environ.get('nuestroclima.pais')}

    app.wsgi_app = ProxyFix(IPDesdeCloudflare(app.wsgi_app), x_for=1)
    return app.test_client()


def test_rangos():
    assert es_cloudflare('172.70.1.1') and es_cloudflare('2606:4700::1')
    assert not es_cloudflare('200.1.2.3') and not es_cloudflare('basura')


def test_desde_cloudflare_usa_ip_y_pais_reales():
    r = _cliente().get('/', headers={'X-Forwarded-For': '172.70.1.1',
                                     'CF-Connecting-IP': '190.24.5.6', 'CF-IPCountry': 'co'})
    assert r.json == {'ip': '190.24.5.6', 'pais': 'CO'}


def test_cabecera_falsa_fuera_de_cloudflare_se_ignora():
    r = _cliente().get('/', headers={'X-Forwarded-For': '200.1.2.3',
                                     'CF-Connecting-IP': '190.24.5.6', 'CF-IPCountry': 'CO'})
    assert r.json == {'ip': '200.1.2.3', 'pais': None}


def test_ip_invalida_de_cloudflare_no_reemplaza():
    r = _cliente().get('/', headers={'X-Forwarded-For': '172.70.1.1', 'CF-Connecting-IP': 'x<script>'})
    assert r.json['ip'] == '172.70.1.1'


def test_obtener_pais_usa_el_de_cloudflare_sin_consultar_afuera(monkeypatch):
    monkeypatch.setattr(sec.requests, 'get', lambda *a, **k: (_ for _ in ()).throw(AssertionError))
    entorno = {'REMOTE_ADDR': '190.24.5.6', 'nuestroclima.pais': 'CO'}
    with Flask(__name__).test_request_context(environ_base=entorno):
        assert sec.obtener_pais('190.24.5.6') == 'CO'
