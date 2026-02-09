#!/bin/bash
echo "Running migrations..."
python manage.py migrate --noinput
echo "Collecting static files..."
python manage.py collectstatic --noinput
echo "Seeding demo data..."
python manage.py seed_demo
echo "Syncing chat channel members..."
python manage.py sync_channel_members
echo "Resetting staff passwords and sending welcome emails..."
python manage.py reset_staff_passwords --login-url https://app.nbnesigns.co.uk/login || true
echo "Starting gunicorn..."
gunicorn config.wsgi --bind 0.0.0.0:$PORT --workers 3 --timeout 120
