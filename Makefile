.PHONY: install install-minimal
.PHONY: createtables createtables-minimal createtables-celery createsuperuser installsysdeps configuresysdeps
.PHONY: run run-celery run-server run-web-server run-minimal run-crawlee-server 
.PHONY: update update-instances static migrate reformat oncommit test create-companion-app
.PHONY: clear clear-crawlee-files clear-celery

CP = cp
PROJECT_NAME = linklibrary
PORT=8080
APP_NAME = rsshistory
# Edit companion app if necessary
COMPANION_APP = catalog

# Assumptions:
#  - python poetry is in your path

install:
	poetry install
	poetry run python -m spacy download en_core_web_sm
	poetry run playwright install
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
	poetry run python -m spacy download en_core_web_sm
	poetry run playwright install
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
	apt -y install rabbitmq-server, memcached, wget, id3v2, chromium-chromedriver
	systemctl enable rabbitmq-server
	systemctl start rabbitmq-server
	systemctl enable memcached.service
	systemctl start memcached.service

run: run-server run-web-server

run-minimal: run-server

run-server: run-script-server run-celery

run-script-server:
	poetry run python script_server.py &

run-celery:
	rm -rf celerybeat-schedule.db
	poetry run celery -A linklibrary worker -l INFO -B

run-web-server:
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

update-instances:
	poetry run python3 workspace.py -U

migrate:
	poetry run python manage.py makemigrations
	poetry run python manage.py migrate

update: update-instances migrate static

test: migrations-check
	@poetry run python manage.py test $(APP_NAME) -v 2

oncommit: reformat test

create-companion-app:
	rm -rf ./$(COMPANION_APP)
	mkdir $(COMPANION_APP)
	cp -r $(APP_NAME)/* ./$(COMPANION_APP)/*
	grep -rl $(APP_NAME) ./$(COMPANION_APP) | xargs sed -i 's/$(APP_NAME)/$(COMPANION_APP)/g'
	@echo "*******************************************************************"
	@echo "Please configure your django application linklibrary in settings.py"
	@echo "Please:"
	@echo " - register app in INSTALLED_APPS, add '$(COMPANION_APP).apps.LinkDatabase',
	@echo "*******************************************************************"

clear: clear-celery clear-crawlee-files

clear-celery:
	rm -f celerybeat-schedule.db

clear-crawlee-files:
	rm -rf storage
