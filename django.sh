#!/bin/bash
set -e

echo "Running migrations"
python manage.py makemigrations
python manage.py migrate

echo "Starting Celery workers"
celery -A your_project worker --loglevel=info &

echo "Starting Celery Beat"
celery -A your_project beat --loglevel=info &

echo "Starting Django server"
python manage.py runserver 0.0.0.0:8000
