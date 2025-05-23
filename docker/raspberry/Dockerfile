# Adapted from https://gist.github.com/soof-golan/6ebb97a792ccd87816c0bda1e6e8b8c2
# This is minimal startup of django app, which uses SQL lite, and no background task like celery

FROM python:3.9 as python-base

FROM python-base as poetry-base

# Creating a virtual environment just for poetry and install it with pip
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools

# Create a new stage from the base python image
FROM python-base as example-app

# Add Poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

COPY requirements.txt ./

RUN pip install -r requirements.txt

# spacy needs a file to be downloaded
# RUN python3 -m spacy download en_core_web_sm
# playwright needs a browser
# RUN playwright install

# Copy Application
COPY . /app

# Copy the custom settings template
COPY ./linklibrary/settings_template_postgres_celery.py /app/linklibrary/settings.py
RUN mkdir -p /app/linklibrary/rsshistory/migrations
RUN touch /app/linklibrary/rsshistory/migrations/__init__.py

# TODO Copy chromedriver to /usr/local/bin
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg id3v2 wget xvfb python3-lxml python3-psycopg2

# Expose the port that Django will run on
EXPOSE 8000

RUN ["chmod", "+x", "/app/docker-entrypoint.sh"]

# TODO how to kill server?
ENTRYPOINT ["/app/docker-entrypoint.sh"]

# Run the Django application using Poetry
#CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
#CMD ["/app/docker-entrypoint.sh"]

# can be further enhanced with
# https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/
# https://stackoverflow.com/questions/33992867/how-do-you-perform-django-database-migrations-when-using-docker-compose
