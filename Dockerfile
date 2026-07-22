# ── Imagen base ligera ──
FROM python:3.11-slim

# Metadatos
LABEL maintainer="Finca Lagunitas" \
      description="Sistema de Monitoreo Climático - Finca Lagunitas, Guavatá, Santander"

# Directorio de trabajo
WORKDIR /app

# Copiar dependencias primero (para aprovechar el caché de capas Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio para persistencia de la BD (se mapeará con un volumen en Coolify)
RUN mkdir -p /app/data

# Exponer el puerto
EXPOSE 8080

# Variables de entorno por defecto
ENV FLASK_ENV=production \
    DB_PATH=/app/data/clima.db

# Comando de producción: Gunicorn con 2 workers
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120", "app:app"]
