View all screenshots: [https://github.com/rumca-js/Django-link-archive/tree/main/screenshots](https://github.com/rumca-js/Django-link-archive/tree/main/screenshots).

# Index

Displays total number of entries, sources, and bookmarks.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/index.PNG)

# Search form

Allows to search links.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/search_form.PNG)

# Entry, link details

Displays entry details.

provides ability to:
 - edit, bookmark, tag, remove, hide link
 - download music, video, or update link data if it is YouTube link
 - view stored snaptshots in archive.org webpage, and make a new snapshot

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entry_details.PNG)

# Tags

Displays all available tags.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/tag_view.PNG)

# Soure list

Displays available sources.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/source_list.PNG)

# Soure details

Displays source details.

Provides ability to:
 - view stored snaptshots in archive.org webpage, and make a new snapshot

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/source_details.PNG)

# Lists are configurable

Display as lines with buttons
![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entries_list_buttons.PNG)

Display as youtube
![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entries_list_youtube.PNG)

# Forms

## New entry form

Allows to add new entry, link. When adding youtube link all fields are set automatically.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/entry_new.PNG)

## New source form

Allows to add new source.

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

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/configuration_page.PNG)

## Server status

Provides server status, information about threads, logged information, import and export logs.

Note: The administrator is required to start threads through link (automated), or through button "Start threads". This was implemented for scenario where django internal server operates privately, and Apache django setup uses database as readonly preview for public.

Server opertion is split between threads and background jobs. Background jobs is a table of 'jobs' that should be handled. Each task can process multiple types of jobs. For example 'write' task can write bookmarks, daily data, download music, download videos, etc.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/server_status.PNG)

## User configuration

Provides user configuration. Each user can configure their view to be shown differently.

![](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/screenshots/user_configuration_page.PNG)
