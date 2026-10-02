# Weather Monitoring System (Flask)

Web system that collects, stores and publishes weather data for a region of Colombia: personal and public weather stations, national hydrological stations (FEWS/IDEAM) and daily NASA satellite imagery. It serves a public dashboard, a rain map and a weekly regional report, and exports data to PDF and Excel. Everything runs in Docker Compose.

![Python](https://img.shields.io/badge/Python-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?logo=flask&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker%20Compose-2496ED?logo=docker&logoColor=white)

## Features

- **Live dashboard** with current readings, history, statistics and a comparison between stations, charted with Chart.js.
- **Rain map** of nearby stations and per-station history.
- **Regional report** (hydrological stations, rivers and alerts) with a PDF version and a weekly summary of minimum and maximum values per municipality.
- **Satellite archive:** one capture per day and layer (GeoColor and infrared, NASA GOES-East). After three months the captures are packed into one compressed file per month, and the database records are kept.
- **Excel export** of historical data and a weekly report sent by email.
- **News section** with an authenticated admin form.
- **Protection:** rate limits by country, email alerts for blocked IPs, optional passkey validation on the station endpoint, CORS allowlist and a maintenance-mode switch.

## Architecture

Seven containers with explicit memory and CPU limits:

| Service | Role |
|---|---|
| `app` | Flask web app and API served by gunicorn |
| `db` | PostgreSQL |
| `redis` | Cache for expensive endpoints |
| `poller` | Pulls readings from the personal station |
| `historial_poller` | Stores daily history of public stations |
| `lecturas_fews_poller` | Daily readings of the hydrological stations |
| `publicador_velez`, `capturas_mapas_poller`, `reporter` | Regional report, satellite captures and weekly email |

```
app/        Flask app: routes, models, templates, static assets
scripts/    independent processes (pollers, importers, reporter)
docs/       documentation
```

## Run it

```bash
git clone https://github.com/cristianyesidmquiroga-tech/Sistema_Clima.git
cd Sistema_Clima
cp .env.example .env     # Windows: copy .env.example .env
# set DB_PASS, WU_API_KEY, STATION_PASSKEY and SMTP_* in .env
docker compose up -d --build
```

Every variable is documented with a comment in `.env.example`. Set `MODO_MANTENIMIENTO=true` to put the site in maintenance mode without touching code.

## Stack

Python, Flask, SQLAlchemy, PostgreSQL, Redis, gunicorn, WeasyPrint, openpyxl, Chart.js, Docker Compose.

## Author

Cristian Muñoz · [GitHub](https://github.com/cristianyesidmquiroga-tech)
