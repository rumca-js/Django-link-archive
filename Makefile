.PHONY: run install test install-optional

statics:
	python -m manage collectstatic

run:
	python -m manage runserver 0.0.0.0:8000

install:
	python -m pip install -r install/requirements.txt
	@django-admin startproject linklibrary
	@echo "Please configure your django application linklibrary (settings.py)"
	@echo " - modify INSTALLED_APPS, add django_user_agents, according to https://pypi.org/project/django-user-agents/"
	@echo " - modify CACHES, to include django user agent MemcachedCache"
	@echo " - modify MIDDLEWARE_CLASSES, add django_user_agents.middleware.UserAgentMiddleware"
	@echo " - modify INSTALLED_APPS, add rsshistory.apps.RssHistoryConfig"

install-optional:
	# I cannot write installation commands for each Linux distro. I assume you are using debian-derivative
	sudo apt -y install wget, id3v2

migrations-check:
	python -m manage makemigrations --check --dry-run

test: migrations-check
	@python manage.py test rsshistory
