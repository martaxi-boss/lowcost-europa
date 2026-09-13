# Lowcost Europa

Lowcost Europa is a private affiliate-platform project focused initially on Portugal. This repository contains the project governance documents and the Django foundation.

## Foundation stack

- Python 3.12
- Django 5.2 LTS
- PostgreSQL 16
- Server-side Django templates
- Ruff for lightweight linting

## Local requirements

Install Python 3.12 and PostgreSQL 16. Create a virtual environment:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements/development.txt
```

## Environment variables

Copy `.env.example` values into your shell or a local `.env` loader of your choice. The application itself deliberately does not depend on a dotenv library.

Required variables are `DJANGO_SECRET_KEY`, `POSTGRES_DB`, `POSTGRES_USER` and `POSTGRES_PASSWORD`. `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `POSTGRES_HOST` and `POSTGRES_PORT` are also configurable. Never commit real credentials.

Example shell configuration:

```bash
export DJANGO_SECRET_KEY='local-only-secret'
export DJANGO_DEBUG=false
export DJANGO_ALLOWED_HOSTS='localhost,127.0.0.1'
export POSTGRES_DB='lowcost_europa'
export POSTGRES_USER='lowcost_europa'
export POSTGRES_PASSWORD='choose-a-local-password'
export POSTGRES_HOST='127.0.0.1'
export POSTGRES_PORT='5432'
```

## Database

Create the PostgreSQL database and role using your local PostgreSQL administration tools, then run:

```bash
python manage.py migrate
python manage.py makemigrations --check --dry-run
```

## Run locally

```bash
python manage.py check
python manage.py runserver
```

Health endpoints:

- `GET /health/live/` — liveness only; does not query PostgreSQL.
- `GET /health/ready/` — readiness; returns 200 only when PostgreSQL is reachable, otherwise 503.

Django Admin remains available at `/admin/` and is not customized in LE-001.

## Tests and lint

Tests use PostgreSQL, never SQLite. Point the environment variables at a PostgreSQL database for which the configured role can create the Django test database, then run:

```bash
DJANGO_SETTINGS_MODULE=config.settings.test python manage.py test
ruff check .
```

The GitHub Actions workflow performs `check`, migration drift validation, migrations, Ruff and automated tests against PostgreSQL 16.

## Environments

Settings live under `config/settings/`: `base.py`, `development.py`, `test.py`, `staging.py` and `production.py`. Staging and production force `DEBUG=False`; deployment of either environment is outside LE-001.

## AliExpress integration

Technical integration documentation: `docs/integrations/aliexpress.md`.

## Project governance

Read `PROJECT_CONSTITUTION.md`, `PROJECT_STATE.md`, `AGENTS.md` and `SUPERVISOR_PROMPT.md` before making structural changes. Development is task → branch → tests → Pull Request → Supervisor review → approval → merge.
