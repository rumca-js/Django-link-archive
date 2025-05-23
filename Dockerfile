# Adapted from https://gist.github.com/soof-golan/6ebb97a792ccd87816c0bda1e6e8b8c2
# This is minimal startup of django app, which uses SQL lite, and no background task like celery

FROM python:3.10 as python-base

# https://python-poetry.org/docs#ci-recommendations
ENV POETRY_VERSION=1.5.0
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VENV=/opt/poetry-venv
# Tell Poetry where to place its cache and virtual environment
ENV POETRY_CACHE_DIR=/opt/.cache

# Create stage for Poetry installation
FROM python-base as poetry-base

# Creating a virtual environment just for poetry and install it with pip
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Create a new stage from the base python image
FROM python-base as example-app

# Copy Poetry to app image
COPY --from=poetry-base ${POETRY_VENV} ${POETRY_VENV}

# Add Poetry to PATH
ENV PATH="${PATH}:${POETRY_VENV}/bin"

WORKDIR /app

# Copy Dependencies
COPY poetry.lock pyproject.toml ./

# [OPTIONAL] Validate the project is properly configured
RUN poetry check

# Install Dependencies
RUN poetry install --no-interaction --no-cache --without dev

# spacy needs a file to be downloaded
RUN poetry run python -m spacy download en_core_web_sm

# Copy Application
COPY . /app

# Copy the custom settings template
COPY ./linklibrary/settings_template_postgres_celery.py /app/linklibrary/settings.py
COPY ./linklibrary/celery_example.py /app/linklibrary/celery.py
COPY ./linklibrary/urls_example.py /app/linklibrary/urls.py

RUN mkdir -p /app/linklibrary/rsshistory/migrations
RUN touch /app/linklibrary/rsshistory/migrations/__init__.py

# TODO Copy chromedriver to /usr/local/bin
RUN apt-get -y update && apt-get -y upgrade && apt-get install -y --no-install-recommends ffmpeg id3v2 wget

# Expose the port that Django will run on
EXPOSE 8000

RUN ["chmod", "+x", "/app/docker-entrypoint.sh"]

# TODO how to kill server?
ENTRYPOINT ["/app/docker-entrypoint.sh"]
