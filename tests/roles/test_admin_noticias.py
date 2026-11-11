from app.models.models import Noticia


def publicar(client, clave, **extra):
    datos = {'clave': clave, 'titulo': 'Lluvia fuerte', 'texto': 'Se esperan tormentas', 'tipo': 'alerta'}
    datos.update(extra)
    return client.post('/admin/noticias', data=datos)


def test_clave_incorrecta_no_publica(client, sesion):
    r = publicar(client, 'mala')
    assert 'Clave incorrecta' in r.get_data(as_text=True)
    assert Noticia.query.count() == 0


def test_clave_correcta_publica(client, sesion):
    publicar(client, 'admin-de-pruebas')
    assert Noticia.query.one().titulo == 'Lluvia fuerte'
    assert client.get('/api/noticias').get_json()[0]['tipo'] == 'alerta'


def test_titulo_vacio_no_publica(client, sesion):
    r = publicar(client, 'admin-de-pruebas', titulo='  ')
    assert 'Falta el título' in r.get_data(as_text=True)
    assert Noticia.query.count() == 0


def test_tipo_desconocido_queda_como_informativa(client, sesion):
    publicar(client, 'admin-de-pruebas', tipo='otro')
    assert Noticia.query.one().tipo == 'informativa'
