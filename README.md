# Overview

 - Django application to manage rss sources
 - Allows to add/remove rss source
 - Each source adds entries to the database

# Features

 - RSS source can be configured, so that entries are deleted after 'X' days
 - RSS entries can be exported to a github repository
 - RSS entry can be marked as 'permament' and will not be deleted
 - RSS entries can be browsed, searched
 - each RSS source contains timestamp when it was fetched, it will not be fetched too often

# Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2022_09_14_entries.PNG)

# Installation

Installation, just as any other Django app.

## Dependencies

 - sudo apt install feedparser / pip3 install feedparser
 - pip3 install python-dateutil
 - pip3 install PyGithub

# Automated export / backup

Provides automated export to github location.

Example: [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)

# Configuration

 - Configuration page allows to define github user / token which allows automatic RSS entries export to repositories
 - You can edit templates, styles
 - You can provide your own RSS feeds
