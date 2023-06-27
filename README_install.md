# Installation overview

Use repository main level Makefile to install and run development server.

Technology stack:
 - django
 - celery - for tasks
 - rabbitmq-server
 - memcached - without it memory locking does not work

Notes:
 - it is best to use on a device with SSD

# Prerequisites

Python poetry [https://python-poetry.org/docs/](https://python-poetry.org/docs/).

# Installation steps (minimal setup)

This is minimal setup, without backend, without tasks.

```
 $ make install-minimal
 Configure settings.py
 Configure rsshistory/prjconfig.py
 $ make createtables-minimal
 $ make createsuperuser
 Configure django users
 $ make run-minimal
```

# Installation steps (full setup)

After performing these steps you should be ready to go. It installs all necessary dependencies, and starts servers.

```
 $ make install
 Configure settings.py
 Configure rsshistory/prjconfig.py
 $ make createtables
 $ make createsuperuser
 $ sudo make installsysdeps
 Configure django users
 $ make run
```

Below are more details.

## settings.py

During install step user is informed that settings.py file should be updated:
 - SECRET_KEY needs to be defined
 - ALLOWED_HOSTS needs to be configured
 - tables need to be created
 - users need to be defined

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

## User

This program allows to configure super user using a rule.

You can create super user manually, as usual in Django [https://www.geeksforgeeks.org/how-to-create-superuser-in-django/](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)

## Using Apache

Django apps can be deployed for Apache: [https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/](https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/).

Notes:
 - You can point apache to use env set up by the poetry

## Demo

Demo on developement env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)

# Monitoring

 - Celery - [https://docs.celeryq.dev/en/stable/userguide/monitoring.html](https://docs.celeryq.dev/en/stable/userguide/monitoring.html)
