# Overview

 - Django application to manage rss sources
 - Allows to add/remove rss source
 - Each source adds entries to the database
 - Entry database is searchable
 - Entries can be starred/added to favourites

# Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2022_09_14_entries.PNG)

# Installation

Installation, just as any other Django app.

## Dependencies

 - sudo apt install feedparser / pip3 install feedparser
 - pip3 install python-dateutil
 - pip3 install PyGithub

# Configuration

 - Configuration page allows to define github user / token which allows automatic RSS entries export to repositories
 - You can edit templates, styles
 - You can provide your own RSS feeds

# Examples

My RSS entry export repository: [github.com](https://github.com/rumca-js/RSS-Link-Database)
