from werkzeug.exceptions import TooManyRequests


def test_el_limite_responde_429_con_espera(app):
    with app.test_request_context('/api/stats'):
        r = app.handle_user_exception(TooManyRequests())
    assert r.status_code == 429
    assert r.headers['Retry-After'] == '60'
