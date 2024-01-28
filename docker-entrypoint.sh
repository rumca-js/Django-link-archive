#!/bin/bash

mkdir -p /app/linklibrary/rsshistory/migrations
touch /app/linklibrary/rsshistory/migrations/__init__.py

# Collect static files
echo "Collect static files"
poetry run python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
# poetry run python manage.py migrate
poetry run python manage.py migrate --run-syncdb

# Start server
echo "Starting server"
poetry run python manage.py runserver 0.0.0.0:8000

echo "Now connect to docker, and define super super"
