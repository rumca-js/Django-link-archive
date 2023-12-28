# Use an official Python runtime as a parent image
FROM python:3.9

# Set environment variables for Python and Poetry
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV POETRY_HOME="/opt/poetry" \
    POETRY_VERSION="1.1.11"

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | bash

# Set the working directory in the container
WORKDIR /app

# Copy the Poetry files and install dependencies
COPY pyproject.toml poetry.lock /app/
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the Django application code into the container
COPY . /app/

# Copy the custom settings template
COPY ./linklibrary/settings_template_default.py /app/settings.py

# Expose the port that Django will run on
EXPOSE 8000

# Run the Django application using Poetry
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
