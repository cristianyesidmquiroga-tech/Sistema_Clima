def test_la_csp_cierra_plugins_base_formularios_e_iframes(app):
    csp = app.test_client().get('/robots.txt').headers['Content-Security-Policy']
    for regla in ("object-src 'none'", "base-uri 'self'", "form-action 'self'", "frame-ancestors 'none'"):
        assert regla in csp, regla
