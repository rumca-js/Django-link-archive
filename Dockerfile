# Use an official Python runtime as a parent image
FROM python:3.10 as python-base

# Set environment variables for Python and Poetry
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME=/opt/poetry
ENV POETRY_VERSION="1.1.11"
ENV POETRY_VENV=/opt/poetry-venv
ENV POETRY_CACHE_DIR=/opt/.cache

# Create stage for Poetry installation
FROM python-base as poetry-base

# Creating a virtual environment just for poetry and install it with pip
RUN python3 -m venv $POETRY_VENV \
	&& $POETRY_VENV/bin/pip install -U pip setuptools \
	&& $POETRY_VENV/bin/pip install poetry==${POETRY_VERSION}

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/

# Copy the Django application code into the container
COPY . /app/

# Copy the custom settings template
COPY ./linklibrary/settings_template_default.py /app/settings.py

# Expose the port that Django will run on
EXPOSE 8000

# Run the Django application using Poetry
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
