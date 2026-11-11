import os
import sys

import pytest

os.environ.setdefault('STATION_PASSKEY', 'clave-de-pruebas')
os.environ.setdefault('ADMIN_PASSKEY', 'admin-de-pruebas')
os.environ.setdefault('DB_USER', 'porteria')
os.environ.setdefault('DB_PASS', 'pruebas')
os.environ.setdefault('DB_HOST', 'localhost')
os.environ.setdefault('DB_PORT', '5432')
os.environ.setdefault('DB_NAME', 'clima_pruebas')

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, cache, limiter  # noqa: E402
from app.models.models import db  # noqa: E402


@pytest.fixture(scope='session')
def app():
    aplicacion = create_app()
    aplicacion.config.update(TESTING=True)
    limiter.enabled = False
    return aplicacion


@pytest.fixture
def client(app):
    with app.app_context():
        for tabla in reversed(db.metadata.sorted_tables):
            db.session.execute(tabla.delete())
        db.session.commit()
    cache.clear()
    return app.test_client()


@pytest.fixture
def sesion(app):
    with app.app_context():
        yield db.session
