# Installation

Use repository main level makefile to install and run development server.

Makefile: [https://github.com/rumca-js/Django-link-archive/blob/main/Makefile](https://github.com/rumca-js/Django-link-archive/blob/main/Makefile).

To install python dependencies & wget & id3v2 using apt
```
make install
```

To start server
```
make run
```

## User

Create super user, as usual in Django [https://www.geeksforgeeks.org/how-to-create-superuser-in-django/](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)
```
python manage.py createsuperuser
```

Create also other users, as required by your setup, environment.

## Notes

 - it is best to use on a device with SSD

## Using Apache

Django apps can be deployed for Apache: [https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/](https://thecodelearners.com/deploy-django-web-application-to-apache-server-step-by-step-guide/).

## Demo

Demo on developement env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)
