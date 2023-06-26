# Installation overview

Use repository main level Makefile to install and run development server.

Technology stack:
 - django, celery, rabbitmq-server

Notes:
 - it is best to use on a device with SSD

# Prerequisites

Python poetry

# Installation steps

```
 $ make install
 Configure settings.py
 Configure rsshistory.prjconfig.py
 $ make createtables
 $ make createsuperuser
 $ sudo make installsysdeps
 Configure django users
 $ make run
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
