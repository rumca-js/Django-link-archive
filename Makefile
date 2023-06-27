.PHONY: install install-minimal
.PHONY: createtables createtables-minimal createtables-celery createsuperuser installsysdeps configuresysdeps
.PHONY: run run-celery runserver run-minimal
.PHONY: reformat static migrate oncommit test 

CP = cp
PROJECT_NAME = linklibrary
APP_NAME = rsshistory
PORT=8080

# Assumptions:
#  - python poetry is in your path

install:
	poetry install
	@$(CP) $(PROJECT_NAME)/settings_template.py $(PROJECT_NAME)/settings.py
	@echo "*******************************************************************"
	@echo "Please configure your django application linklibrary in settings.py"
	@echo "Please:"
	@echo " - define SECRET_KEY settings.py"
	@echo " - use createtables rule to create tables"
	@echo " - add required hosts to ALLOWED_HOSTS"
	@echo "*******************************************************************"

install-minimal:
	poetry install
	@$(CP) $(PROJECT_NAME)/settings_template_minimal.py $(PROJECT_NAME)/settings.py
	@echo "*******************************************************************"
	@echo "Please configure your django application linklibrary in settings.py"
	@echo "Please:"
	@echo " - define SECRET_KEY settings.py"
	@echo " - use createtables rule to create tables"
	@echo " - add required hosts to ALLOWED_HOSTS"
	@echo "*******************************************************************"

createtables: createtables-minimal createtables-celery

createtables-minimal:
	poetry run python manage.py migrate --run-syncdb

createtables-celery:
	poetry run python manage.py migrate django_celery_results

createsuperuser:
	poetry run python manage.py createsuperuser

# Assumptions:
# - I cannot write installation commands for each Linux distro. I assume you are using debian-derivative
# - assume you are using sudo for this command. solve it later https://github.com/rumca-js/Django-link-archive/issues/10
# http://pont.ist/rabbit-mq/
installsysdeps:
	apt -y install rabbitmq-server, memcached, wget, id3v2
	systemctl enable rabbitmq-server
	systemctl start rabbitmq-server
	systemctl enable memcached.service
	systemctl start memcached.service

run: run-celery runserver

run-minimal: runserver

run-celery:
	poetry run celery -A linklibrary worker -l INFO -B &

runserver:
	poetry run python manage.py runserver 0.0.0.0:$(PORT)

# Assumptions:
#  - python black is in your path
# Black should use gitignore files to ignore refactoring
reformat:
	poetry run black $(APP_NAME)

static:
	poetry run python -m manage collectstatic

migrations-check:
	poetry run python -m manage makemigrations --check --dry-run

migrate:
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

test: migrations-check
	@poetry run python manage.py test $(APP_NAME)

oncommit: reformat test

