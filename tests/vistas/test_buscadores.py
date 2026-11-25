def test_robots_deja_indexar_y_apunta_al_sitemap(client):
    r = client.get('/robots.txt')
    assert r.status_code == 200 and r.mimetype == 'text/plain'
    texto = r.get_data(as_text=True)
    assert 'Disallow: /admin/' in texto
    assert 'Sitemap: https://www.nuestroclima.co/sitemap.xml' in texto


def test_el_sitemap_lista_paginas_que_existen(client):
    xml = client.get('/sitemap.xml').get_data(as_text=True)
    rutas = [loc.split('nuestroclima.co', 1)[1] for loc in xml.split('<loc>')[1:]]
    rutas = [r.split('</loc>')[0] for r in rutas]
    assert '/' in rutas
    for ruta in rutas:
        assert client.get(ruta).status_code == 200, ruta


def test_llms_resume_el_sitio_sin_datos_personales(client):
    texto = client.get('/llms.txt').get_data(as_text=True)
    assert texto.startswith("# Nuestro Clima")
    assert 'Lagunitas' not in texto
