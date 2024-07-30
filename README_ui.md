
This project is work in progress.
Some screenshots might be little out of date.

You can try try checking official demo on [renegat0x0.ddns.net](https://renegat0x0.ddns.net/apps/places/entries-recent/).

Pinky promise the app will be up, and running.

# Index

Displays index page. Can be customized by a template file

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/index.PNG)

# Link lists

Available link display types
 - standard view
 - lists with buttons
 - similar to YouTube

## YouTube list

Application provides a youtube list view.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entries_list_youtube.PNG)

## Standard list

Application provides a standard list view.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entries_list_standard.PNG)

## List with buttons

Application provides a list with buttons view.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entries_list_buttons.PNG)

# Search form

Allows to search links.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/search_form_omni.PNG)

There are also variations of it

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/search_form_whats_new.PNG)

# Entry, link details

Link details view.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entry_details.PNG)

# Source list

Displays available sources.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/source_list.PNG)

# Soure details

Displays source details.

Provides ability to:
 - view stored snaptshots in archive.org webpage, and make a new snapshot
 - download all youtube video links from a defined channel

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/source_details.PNG)

# Tags

Displays all available tags.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/tags_view.PNG)

# Keywords

Displays all available keywords. The default time span of keywords is 1 day.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/keywords_view.PNG)

## Page properties

Each link can be verified to display HTML properties.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/page_properties.PNG)

# Forms

Most of forms are designed to use Django Model forms.

## New entry form

There are two stages of adding a new link:
 - first you specify a link inside of a simple input form
 - for the link all data are obtained
 - then in second form you will be asked to make your manual edits

## Simple UI for adding a link

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entry_new_simple.PNG)

## Advanced UI for adding a link

Advanced UI for adding a new link

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entry_new.PNG)

## New source form

Allows to add new source.

Similarly to entries, first you have to specify a link to feed, then you can make additional changes.

Currently supported sources:
 - RSS
 - parse mechanism that fetches all links from source URL through web scraping

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/source_new.PNG)

# Admin

## Configuration page

Provides program configuration.

Configuration options:
 - export path provides where exported data are located
 - sources refresh period - how often sources are checked for new links. Each source has its own refresh period.
 - git options allow to provide automated export

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/configuration_form.PNG)

## Server status

Provides server status.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/server_status.PNG)

## User configuration

Provides user configuration. Each user can configure their view to be shown differently.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/user_configuration_view.PNG)

## Logs

All events are stored for maintanance.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/logs_view.PNG)

## Background jobs

Background jobs

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/backgroundjobs_view.PNG)
