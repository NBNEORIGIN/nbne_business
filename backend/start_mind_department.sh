#!/bin/bash
echo "Running migrations..."
python manage.py migrate --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Seeding Mind Department data..."
python manage.py seed_mind_department
echo "Starting gunicorn..."
gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
