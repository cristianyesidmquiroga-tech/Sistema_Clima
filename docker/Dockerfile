FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=run.py
ENV FLASK_ENV=production

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Make entrypoint executable
RUN chmod +x docker/entrypoint.sh

# Expose port 8080 (Sistema Clima port)
EXPOSE 8080

# Run entrypoint: creates admin user + starts Flask server
ENTRYPOINT ["./docker/entrypoint.sh"]
