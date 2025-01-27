# Docker

Docker image is available at [hub.docker.com](https://hub.docker.com/r/rozbujnik/django-link-archive)

Notes:

 - configure docker-compose.yml according to your own setup
 - the image by default uses 'admin' user, with 'admin' password
 - django can be accessed locally with 127.0.0.1:8000, via browser
 - after running the docker image you will be asked to login, and to configure the instance
 - you scan check 'browsers' if they work using page properties page
 - you should check 'sources' to enable some of them

# Overview

This project uses the following technologies:
 - django
 - celery - background task processing
 - database - postgresql
 - rabbitmq-server
 - crawlerbuddy - project that crawls the web [GitHub](https://github.com/rumca-js/crawler-buddy)
 - spacy - for text/keyword analysis

# Manual installation

## Prerequisites

 - Python poetry [https://python-poetry.org/docs/](https://python-poetry.org/docs/).
 - [Crawling program](https://github.com/rumca-js/crawler-buddy)
 - postgresql - use of SQLite is discouraged

Steps:
 - [Basic installation](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#basic-intallation)
 - [Full installation](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#full-intallation)
 - [Configure](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#configure)
 - [Run](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#run)
 - [Advanced](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#advanced)

Notes:
 - it is best to use on a device with SSD
 - do not use SQLlite for production, or more advanced setups https://docs.djangoproject.com/en/5.0/ref/databases/#sqlite-notes

# Basic installation

This is minimal setup, without backend, without tasks.

```
 $ make install-minimal
  - Configure file settings.py
  - Configure file rsshistory/prjconfig.py
 $ make createtables-minimal
 $ make createsuperuser
  - Configure django users
```

For basic setup this should be enough, and should be working.

# Full installation

For a full setup, with backend and tasks a more robust setup needs to be created:

```
 $ make install
  - Configure file settings.py
  - Configure file rsshistory/prjconfig.py
 $ make createtables
 $ make createsuperuser
 $ sudo make installsysdeps
  - Configure django users
```

Parts of it are described below.

# Configure

## settings.py

Django [Settings](https://docs.djangoproject.com/en/5.0/ref/settings/) are most important part of the configuration

During install step user is informed that settings.py file should be updated:
 - SECRET_KEY needs to be defined
 - ALLOWED_HOSTS needs to be configured
 - tables need to be created
 - users need to be defined

## User management

This program allows to configure super user using a rule.

You can create super user manually, as usual in Django [https://www.geeksforgeeks.org/how-to-create-superuser-in-django/](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)

## Run

For minimal setup

```
 $ make run-minimal
```

For full setup
```
 $ make run
```

## Script server *optional*

With django script_server.py server could be started. The server is responsible for scraping handling requests for pages. This feature is optional.

## Setup

After starting django application define RSS sources, start using app.

# Advanced

## Update

After updating source code, to correctly update existing environment please:
```
 $ make update
```

## Makefile

Makefile: [https://github.com/rumca-js/Django-link-archive/blob/main/Makefile](https://github.com/rumca-js/Django-link-archive/blob/main/Makefile).

list of rules:
```
$ make install - installs dependencies, creates settings.py
$ make createtables - creates database tables
$ make createsuperuser - creates super user for the system
$ make installsysdeps - install system dependencies, like rabbitmq-server
$ make run - starts django server and celery
$ make test - performs tests
$ make oncommit - cleans code, runs tests, things needed before making a commit
```

## Manual installation

Read contents of the makefile, and perform the actions described by it

## System dependencies

Makefile assumes you are running debian, or debian compliant OS. To be able to run it on a different system you have to update Makefile accordingly.

This program installs and configures rabbitmq-server in rule make installsysdeps.
If you require redis, or other setup please modify mmakefile accordingly.

To be able to perform various operations additional programs are needed:
 - wget - to download pages
 - id3v2 - to tag downloaded songs

Memcached is required for the memory locking to work.

These programs are installed by make installsysdeps rule.

## Using Apache

Django apps can be deployed for Apache: [https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/](https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/).

Notes:
 - You can point apache to use env set up by the poetry

## Demo

Demo on developement env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)

# Monitoring

 - Celery - [https://docs.celeryq.dev/en/stable/userguide/monitoring.html](https://docs.celeryq.dev/en/stable/userguide/monitoring.html)

# Using the crawling system

You should not plan on doing anything hostile. For you it might be just web scraping. For others it could be DDOS attack.

Some scraping solutions do not work on Raspberry PI out of the box: for example chrome-undetected.

Links:

 - https://medium.com/codex/the-biggest-web-scraping-roadblocks-and-how-to-avoid-them-669125b886b9
 - https://crawlee.dev/docs/guides/avoid-blocking
 - https://docs.apify.com/academy/anti-scraping/mitigation/generating-fingerprints
 - https://docs.apify.com/academy/anti-scraping/mitigation/cloudflare-challenge.md
