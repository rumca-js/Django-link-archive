# Installation overview

Use repository main level Makefile to install and run development server.

This project uses the following technologies:
 - django
 - celery
 - rabbitmq-server
 - memcached - without it memory locking does not work

Steps:
 - [Prerequisites](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#prerequisites)
 - [Basic installation](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#basic-intallation)
 - [Full installation](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#full-intallation)
 - [Configure](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#configure)
 - [Run](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#run)
 - [Advanced](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md#advanced)

Notes:
 - it is best to use on a device with SSD

# Prerequisites

Python poetry [https://python-poetry.org/docs/](https://python-poetry.org/docs/).

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

During install step user is informed that settings.py file should be updated:
 - SECRET_KEY needs to be defined
 - ALLOWED_HOSTS needs to be configured
 - tables need to be created
 - users need to be defined

## User management

This program allows to configure super user using a rule.

You can create super user manually, as usual in Django [https://www.geeksforgeeks.org/how-to-create-superuser-in-django/](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)

## RSS

To enable RSS functionality, you have to provide RSS sources by the page UI.

## Run

For minimal setup

```
 $ make run-minimal
```

For full setup
```
 $ make run
```

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
