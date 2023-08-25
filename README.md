Personal link database, with RSS functionality. Similar to Reddit, but completely open source, on your local machine.

# Features

 - Local data, no algorithms, no advertisements
 - Web GUI, accessible from anywhere (LAN, public, however it is configured)
 - Minimal installation, integrator may choose however to use production environment, with a good Database engine. Just as it is supported by Django. I am using SQLite without any problems.
 - Sources management: adding, removing, configuration
 - Link management: manual adding, removing, configuration, bookmark support, tag support, admin user comments
 - RSS feed support
 - Search ability (Google-like), by language, author, tags
 - Minimal aesthetic: no distraction, compact layout
 - Automatic git export, RSS source import
 - Support for web archive: archive.org
 - Ability to extend, to provide custom plugins, parse HTML pages
 - Configurable: lists, timeouts
 - Since it is a Django page, you can show it to your friends (if you like)

## Problems with other RSS readers, or apps

 - Most RSS clients do not allow manual link input
 - Some programs are not programs from users perspective, but a service:
     * Feedly
     * Pockets
     * Readwise Reader
 - Most programs fail to provide consistent and exhaustive search ability (NextCloud "News" application, Thunderbird, Feeder Android app, Newsboat Linux app)
 - Most programs do not provide ability to add tag to a link (Thunderbird, Android Feeder app)
 - Scale: Lemmy software is replacement for Reddit, but requires a lot of resources to operate. This project aims to provide "single user" experience
 - Goal: Reddit, Lemmy aim is to provide social media experience, this project aims to grant the ability to create database of links
 - Extensions: In Django project it is relatively easy to add new view
 - License: Reddit is a nice project, but it is not entirely open source
 - Interface: Most of the programs are clients (Thunderbird, Feeder, Newsboat), where it is needed to create app that works as a server, so that it can be managed from all devices in LAN, or in public space, if it is configured to operate in that mode

## Possible use cases

 - YouTube filter. You add only your own subscriptions. You can categorize, filter entries from your sources
 - Link aggregator. Similar to Lemmy, Reddit
 - Database of important links: for work, or for school
 - RSS client
 - Data analysis - analyze link rot, how many a page is cited by other sources, analyze link domains. For example [https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md)

## Suite of projects

 - Captured using Django application, program: [https://github.com/rumca-js/Django-link-archive](https://github.com/rumca-js/Django-link-archive)
 - Bookmarked links [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)
 - daily RSS Git repository for the year 2023 [https://github.com/rumca-js/RSS-Link-Database-2023](https://github.com/rumca-js/RSS-Link-Database-2023)
 - daily RSS Git repository for the year 2022 [https://github.com/rumca-js/RSS-Link-Database-2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - daily RSS Git repository for the year 2021 [https://github.com/rumca-js/RSS-Link-Database-2021](https://github.com/rumca-js/RSS-Link-Database-2021)
 - daily RSS Git repository for the year 2020 [https://github.com/rumca-js/RSS-Link-Database-2020](https://github.com/rumca-js/RSS-Link-Database-2020)

## UI

UI, with snapshots, is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_ui.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_ui.md).

## Installation

Installation, and configuration is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md).

## Demo

Demo on development env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)

# Inspiration, notes about search algorithms

README about search issues: [https://github.com/rumca-js/Django-link-archive/blob/main/README_search.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_search.md).

# Import, export data

## View data

Most of views contain "Show JSON" button that provides the view data as JSON. This can be used by scripts, for import, export.

## Automatic git export

Program maintains two repositories: one for bookmarked links, and daily repository.

Each day bookmarks and daily repositories are updated with new data. Daily repository is updated when day finishes, then the complete daily data are pushed into the repository.

### Bookmarks

 - three file formats: JSON, markdown, RSS
 - contains articles that I have selected as interesting, or noteworthy, or funny, or whatever
 - files are split by 'language' and 'year' categories
 - markdown file is generated as a form of preview, JSON can be reused, imported
 - links are bookmarked, but that does not necessarily mean something is endorsed. It shows particular interest in topic. It is indication of importance
 
### Daily Data

 - RSS links are captured for each source separately
 - two files formats for each day and source: JSON and markdown
 - markdown file is generated as a form of preview, JSON can be reused, imported

### Sources

 - provided in sources.json file
 - provides information about sources, like: title, url, langugage

## Import from another Django-link-archive instance

Scenario to import sources from a other instance:
 - find sources in the other instance. It should be at "Sources" menu button, by default
 - select which sources you would like to export, you can select a filter
 - click 'Show as json', it should produce a nice JSON output
 - copy link URL of that instance, of that JSON output
 - navigate to your instance
 - select 'Admin' page
 - select 'Import from URL', and paste URL

Scenario to import links from a other instance:
 - find links in the other instance. It should be at "Search" menu button, by default
 - select which links you would like to export, you can select a filter, like a date, tag. etc.
 - click 'Show as json', it should produce a nice JSON output
 - copy link URL of that instance, of that JSON output
 - navigate to your instance
 - select 'Admin' page
 - select 'Import from URL', and paste URL

# User management

This was created for the single player experience only, but... there is support for more Users.

What works?
 - nearly everything for single player experience

Roadmap for the end game.

 - at first only administrator can add new users. For running instance contact administrator
 - you do not create passwords, they are generated for you, with a proper complexity. Please write them down
 - contact other users, other users can also add new users, if karma allows it

Karma effect on the user:
 - if your karma goes below 0 your account is banned
 - after certain threshold you can submit new links
 - after certain threshold you can submit comments
 - after certain threshold you can upvote and downvote comments
 - after certain threshold you create users (1 per day)

What causes karma change:
 - admin, or moderators
 - adding vote for a link
 - upvotes, or downvotes on comments
 - bans of other users you invited

# Development

Development is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_development.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_development.md).

# Data analysis

With these data we can perform further analysis:

 - how many of old links are not any longer valid (link rot test)
 - capture all domains from RSS links (internal, and leading outside?). Analyse which domains are most common
 - which site generates most entries
 - we can capture all external links from entries, to capture where these sites lead to (check network effect, etc)
 - we can verify who reported first on certain topics
 - we can find all domains that are used by this instance. For example [https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md)

# Analysis of tools and services

Archive.org:
 - Is not reliable. Sometimes it gets painfully slow. It is still better than nothing
 - Most mainstream media RSS is covered, but the coverage is spotty. Not all days are covered
 - Internet Archive (archive.org) does not provide snapshots for each and every day for all RSS sources. It is sometimes pretty slow. We would like to be sure that a such snapshot takes place. Therefore we need to export links to daily repo ourselves. Django RSS app also makes requests to archive to make the snapshots

archive.ph:
 - does not support link + date URL interface

# Legal

 - I do not endorse any link every link in the database. I may some links be important because of how bad the content is. I use irony often, therefore beware!
 - Everyone has a right to be forgotten. If any link should be removed from a database please contact me
 - I do not obtain any form of monetary recompensation from link, or data about it. The data link information were already provided by RSS sources. The RSS source is responsible for what they provide free of charge

# Ending notes

All links belong to us!

