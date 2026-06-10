# Bookstore API

A Python/Django-based REST API for a bookstore application, designed as a development pet project.

This repository demonstrates a local Docker-based development environment with PostgreSQL, Redis, Celery Worker, and Celery Beat.

## Project Overview

- Django REST API
- PostgreSQL 17 for relational storage
- Redis 7 as Celery broker and cache
- Celery worker for asynchronous task processing
- Celery Beat for periodic scheduled tasks

## Project Status

This is a pet project intended for learning, experimentation, and local development. It is not configured for production deployment.

## Tech Stack

- Python 3.12
- Django 5.1
- Django REST Framework
- Celery 5
- Redis 7
- PostgreSQL 17
- Docker and Docker Compose

## Local Development

The project is configured to run locally with Docker Compose. The service definitions are available in `docker-compose.yml` and the application image is built from `Dockerfile`.

### Start the application

```bash
docker compose up --build
```

This command will start the following services:

- `db` — PostgreSQL database
- `redis` — Redis broker/cache
- `web` — Django development server on `http://localhost:8000`
- `celery_worker` — Celery background worker
- `celery_beat` — Celery periodic task scheduler

### Environment variables

A sample configuration file is provided in `.env.example`. Copy it to `.env` and update the values as needed before running the application.

```bash
cp .env.example .env
```

### Apply database migrations

If the database is not yet initialized, apply migrations inside the running `web` container:

```bash
docker compose exec web python manage.py migrate --noinput
```

### Create an admin user

Create a Django superuser for admin access:

```bash
docker compose exec web python manage.py createsuperuser
```

### Stop the environment

```bash
docker compose down
```

## Notes

- Keep `.env` local and do not commit it to the repository.
- The repository includes `.env.example` for configuration placeholders.
- This setup is optimized for local development and testing only.

## GitHub Best Practices

- Do not commit `.venv`, `.env`, or generated media files.
- Keep secret keys and passwords out of the repository.
- Use `.gitignore` and `.dockerignore` to exclude local and environment-specific files.
