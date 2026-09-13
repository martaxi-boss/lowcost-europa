# ADR-001 — Initial architecture

## Status

Accepted

## Decision

Lowcost Europa starts with Python 3.12, Django 5.2 LTS, PostgreSQL 16, a modular monolith and Django server-side templates. Sensitive configuration is supplied through environment variables. Nginx will be introduced when staging or publication exists. Scheduled work will start with Django management commands plus cron or systemd timers before any queueing system is considered.

## Reasons

- Simplicity and low operating cost.
- Easy maintenance and a single deployable application.
- Excellent server-rendered SEO support.
- Strong relational model and migrations with PostgreSQL.
- Django Admin for internal operations without a custom backoffice.
- Appropriate capacity for the initial size of the project.
- Room to grow without premature distributed systems.

## Alternatives rejected in this phase

Microservices, Kubernetes, Elasticsearch, a separate React/SPA or Next.js application, Redis/Celery and other distributed systems are not justified now. They are not permanently forbidden; they require a future measurable need and Supervisor approval.

## Consequences

The application remains one modular codebase with one primary relational database. Module boundaries, migrations and background work must remain disciplined. Staging, Nginx and production infrastructure are separate future decisions.
