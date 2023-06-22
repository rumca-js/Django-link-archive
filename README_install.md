# Installation

Use repository main level makefile to install and run development server.

Prerequisites:
 - python poetry

## Automated installation

Makefile: [https://github.com/rumca-js/Django-link-archive/blob/main/Makefile](https://github.com/rumca-js/Django-link-archive/blob/main/Makefile).

Rules:
```
$ make install - installs dependencies, creates settings.py
$ make createdb - creates database tables
$ make run - starts server
$ make test - performs tests
$ make superuser - creates super user
```

## Manual installation

Read contents of the makefile, and perform the actions described by it

## Other dependencies

To be able to perform various operations additional programs are needed:
 - wget - to download pages
 - id3v2 - to tag downloaded songs

To install them perform the following rule with sudo priviliges
```
make install-optional
```

## User

Create super user, as usual in Django [https://www.geeksforgeeks.org/how-to-create-superuser-in-django/](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)

Use rule.

Create also other users, as required by your setup, environment.

## Notes

 - it is best to use on a device with SSD

## Using Apache

Django apps can be deployed for Apache: [https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/](https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/).

## Demo

Demo on developement env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)
