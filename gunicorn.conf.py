bind = "0.0.0.0:8080"
workers = 2
timeout = 60
preload_app = True


def post_fork(server, worker):
    """
    Con preload_app=True, el proceso master importa la app (y crea el
    engine de SQLAlchemy) antes de bifurcar los workers. Sin este hook,
    los workers heredan y comparten la misma conexion TCP a Postgres,
    lo que corrompe el protocolo cuando dos workers la usan a la vez
    ("lost synchronization with server"). Aca se descarta el pool
    heredado para que cada worker abra sus propias conexiones nuevas.
    """
    from run import app
    from app.models.models import db
    with app.app_context():
        db.engine.dispose()
    server.log.info("Worker %s: conexiones a la base de datos reiniciadas tras el fork", worker.pid)
