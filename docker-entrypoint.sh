#!/bin/bash


if ! test -f /app/linklibrary/initialized.txt; then
  mkdir -p /app/linklibrary/rsshistory/migrations
  touch /app/linklibrary/rsshistory/migrations/__init__.py
  
  # Collect static files
  echo "Collect static files"
  poetry run python manage.py collectstatic --noinput
  
  # Apply database migrations
  echo "Apply database migrations"
  poetry run python manage.py makemigrations
  poetry run python manage.py migrate auth
  echo "Apply database clean migrate"
  poetry run python manage.py migrate
  echo "Apply database clean migrate - rsync"
  poetry run python manage.py migrate --run-syncdb
  
  echo "Creating user"
  if [ -z "${DJANGO_SUPERUSER_USERNAME}" ]; then 
      FOO_USER='admin'
  else 
      FOO_USER=${DJANGO_SUPERUSER_USERNAME}
  fi
  
  if [ -z "${DJANGO_SUPERUSER_PASSWORD}" ]; then 
      export DJANGO_SUPERUSER_PASSWORD='admin'
  else 
      export FOO_PASSWORD=${DJANGO_SUPERUSER_PASSWORD}
  fi
  
  if [ -z "${DJANGO_SUPERUSER_EMAIL}" ]; then 
      export DJANGO_SUPERUSER_EMAIL='no@email.com'
  fi
  
  poetry run python manage.py createsuperuser \
    --noinput \
    --username $FOO_USER \
    --email "${DJANGO_SUPERUSER_EMAIL}" \

fi

touch /app/linklibrary/initialized.txt
mkdir -p /app/linklibrary/lesson-11/broker/queue

echo "Starting workers"
poetry run python manage.py threadprocessor --thread RefreshProcessor &
poetry run python manage.py threadprocessor --thread SourceJobsProcessor &
poetry run python manage.py threadprocessor --thread WriteJobsProcessor &
poetry run python manage.py threadprocessor --thread ImportJobsProcessor &
poetry run python manage.py threadprocessor --thread SystemJobsProcessor &
poetry run python manage.py threadprocessor --thread UpdateJobsProcessor &
poetry run python manage.py threadprocessor --thread LeftOverJobsProcessor &
poetry run python manage.py threadprocessor --thread BlockJobsProcessor &

echo "Starting web server"
poetry run python manage.py runserver 0.0.0.0:8000

echo "Now connect to docker, and define super super"
