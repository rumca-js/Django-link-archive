.PHONY: run install test install-optional reformat createdb static migrate superuser

CP = cp
PROJECT_NAME = linklibrary
APP_NAME = rsshistory

# Assumptions:
#  - python poetry is in your path

install:
	poetry install
	@$(CP) $(PROJECT_NAME)/settings_template.py $(PROJECT_NAME)/settings.py
	@echo "*******************************************************************"
	@echo "Please configure your django application linklibrary in settings.py"
	@echo "Please:"
	@echo " - define SECRET_KEY settings.py"
	@echo " - use createdb rule to create tables"
	@echo " - add required hosts to ALLOWED_HOSTS"
	@echo "*******************************************************************"

createdb:
	poetry run python manage.py migrate --run-syncdb 

install-optional:
	# Assumptions:
	# - I cannot write installation commands for each Linux distro. I assume you are using debian-derivative
	# - assume you are using sudo for this command. solve it later https://github.com/rumca-js/Django-link-archive/issues/10
	apt -y install wget, id3v2

run:
	bash -c "sleep 10; wget -q -S http://127.0.0.1:8080/rsshistory/start-background-threads" &
	poetry run python manage.py runserver 0.0.0.0:8080

migrations-check:
	poetry run python -m manage makemigrations --check --dry-run

static:
	poetry run python -m manage collectstatic

migrate:
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

test: migrations-check
	@poetry run python manage.py test $(APP_NAME)

reformat:
	# Assumptions:
	#  - python black is in your path
	# Black should use gitignore files to ignore refactoring
	black $(APP_NAME)

superuser:
	poetry run python manage.py createsuperuser
