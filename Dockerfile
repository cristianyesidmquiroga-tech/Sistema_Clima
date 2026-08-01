FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev \
        libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf-2.0-0 libffi-dev shared-mime-info && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Carpetas donde montan los volumenes con nombre (docker-compose.yml):
# tienen que existir ya en la imagen con el dueno correcto, porque Docker
# solo copia el contenido inicial del volumen (con sus permisos) la
# primera vez que se monta - si no existieran aqui, el volumen quedaria
# de root y el proceso (que corre como appuser, sin privilegios) no
# podria escribir en el.
RUN mkdir -p app/static/img/reporte-velez/capturas archivo_datos/capturas_mapas app/static/uploads/noticias

RUN useradd --create-home --shell /bin/false appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
