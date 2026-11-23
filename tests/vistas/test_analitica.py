def test_sin_token_no_carga_analitica(client):
    html = client.get('/').get_data(as_text=True)
    assert 'cloudflareinsights' not in html


def test_con_token_carga_el_beacon(client, monkeypatch):
    monkeypatch.setenv('CLOUDFLARE_ANALYTICS_TOKEN', 'tok_de_prueba')
    html = client.get('/').get_data(as_text=True)
    assert 'static.cloudflareinsights.com/beacon.min.js' in html
    assert 'tok_de_prueba' in html
