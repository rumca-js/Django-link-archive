.PHONY: run install test install-optional refresh

statics:
	poetry run python -m manage collectstatic

run:
	poetry run python -m manage runserver 0.0.0.0:8000

install:
	poetry install
	@django-admin startproject linklibrary
	@echo "Please configure your django application linklibrary (settings.py)"
	@echo " - modify INSTALLED_APPS, add django_user_agents, according to https://pypi.org/project/django-user-agents/"
	@echo " - modify CACHES, to include django user agent MemcachedCache"
	@echo " - modify MIDDLEWARE_CLASSES, add django_user_agents.middleware.UserAgentMiddleware"
	@echo " - modify INSTALLED_APPS, add rsshistory.apps.RssHistoryConfig"

install-optional:
	# Assumptions:
	# - I cannot write installation commands for each Linux distro. I assume you are using debian-derivative
	# - assume you are using sudo for this command. solve it later https://github.com/rumca-js/Django-link-archive/issues/10
	apt -y install wget, id3v2

migrations-check:
	poetry run python -m manage makemigrations --check --dry-run

test: migrations-check
	@poetry run python manage.py test rsshistory

refresh:
	poetry export -f requirements.txt --output install/requirements.txt
