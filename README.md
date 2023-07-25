Personal link database, with RSS functionality. Similar to Reddit, but completely open source, on your local machine.

# Features

 - Local data, no algorithms, no advertisements
 - Web GUI, accessible from anywhere (LAN, public, however it is configured)
 - Search ability (Google-like), by language, author, tags
 - Ability to extend, to provide custom plugins, parse HTML pages
 - RSS feed support (RSS sources)
 - Sources management: adding, removing, configuration
 - Link management: manual adding, removing, configuration, bookmark support, tag support, admin user comments
 - Minimal aesthetic: no distraction, compact layout
 - Configurable: lists, timeouts
 - Automatic git export, RSS source import
 - Minimal installation, integrator may choose however to use production environment, with a good Database engine. Just as it is supported by Django. I am using SQLite without any problems.
 - Support for web archive
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

 - YouTube link database, link aggregator
 - Database of important links: for work, for school
 - RSS client
 - Reddit/lemmy/diggit replacement
 - Data analysis - analyze link rot, how many a page is cited by other sources. For example [https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md](https://raw.githubusercontent.com/rumca-js/Django-link-archive/main/analysis_domains.md)
 - YouTube filter. Manage your own subscriptions, videos, without thirdparty interference

## UI

UI, with snapshots, is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_ui.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_ui.md).

## Installation

Installation is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md).

To configure you need to add sources. There are at least two types:
 - standard RSS source
 - parsed source. For this source page contents is downloaded, and links from it are extracted from that page and added to the database

How to find RSS link? There is a 'tutorial' for that: [https://zapier.com/blog/how-to-find-rss-feed-url/](https://zapier.com/blog/how-to-find-rss-feed-url/)

## Suite of projects

 - Captured using Django application: [https://github.com/rumca-js/Django-link-archive](https://github.com/rumca-js/Django-link-archive)
 - Bookmarked links [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)
 - daily RSS Git repository for the year 2023 [https://github.com/rumca-js/RSS-Link-Database-2023](https://github.com/rumca-js/RSS-Link-Database-2023)
 - daily RSS Git repository for the year 2022 [https://github.com/rumca-js/RSS-Link-Database-2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - daily RSS Git repository for the year 2021 [https://github.com/rumca-js/RSS-Link-Database-2021](https://github.com/rumca-js/RSS-Link-Database-2021)
 - daily RSS Git repository for the year 2020 [https://github.com/rumca-js/RSS-Link-Database-2020](https://github.com/rumca-js/RSS-Link-Database-2020)

## Demo

Demo on development env (may, or may not be running actually):
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/)

# Inspiration, notes about search algorithms

README about search issues: [https://github.com/rumca-js/Django-link-archive/blob/main/README_search.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_search.md).

## Development

Development is described by a separate README: [https://github.com/rumca-js/Django-link-archive/blob/main/README_development.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_development.md).

# Import, export data

Program maintains two repositories: one for bookmarked links, and daily repository.

Each day bookmarks and daily repositories are updated with new data. Daily repository is updated when day finishes, then the complete daily data are pushed into the repository.

Link properties:
 - persistent - set if it is bookmarked
 - tag - set by the users, through forms
 - vote - set by the users, through forms. Decides how important the link is. Admin can arbitrarily define how long the range is

## Bookmarks

 - three file formats: JSON, markdown, RSS
 - contains articles that I have selected as interesting, or noteworthy, or funny, or whatever
 - files are split by 'language' and 'year' categories
 - markdown file is generated as a form of preview, JSON can be reused, imported
 - links are bookmarked, but that does not necessarily mean something is endorsed. It shows particular interest in topic. It is indication of importance
 
## Daily Data

 - RSS links are captured for each source separately
 - two files formats for each day and source: JSON and markdown
 - markdown file is generated as a form of preview, JSON can be reused, imported

## Sources

 - provided in sources.json file
 - provides information about sources, like: title, url, langugage

## Data analysis

With these data we can perform further analysis:

 - how many of old links are not any longer valid (link rot test)
 - capture all domains from RSS links (internal, and leading outside?). Analyse which domains are most common
 - which site generates most entries
 - we can capture all external links from entries, to capture where these sites lead to (check network effect, etc)
 - we can verify who reported first on certain topics

## Analysis of tools and services

Archive.org:
 - Is not reliable. Sometimes it gets painfully slow. It is still better than nothing
 - Most mainstream media RSS is covered, but the coverage is spotty. Not all days are covered
 - Internet Archive (archive.org) does not provide snapshots for each and every day for all RSS sources. It is sometimes pretty slow. We would like to be sure that a such snapshot takes place. Therefore we need to export links to daily repo ourselves. Django RSS app also makes requests to archive to make the snapshots

archive.ph:
 - does not support link + date URL interface

## Legal

 - I do not endorse any link every link in the database. I may some links be important because of how bad the content is. I use irony often, therefore beware!
 - Everyone has a right to be forgotten. If any link should be removed from a database please contact me
 - I do not obtain any form of monetary recompensation from link, or data about it. The data link information were already provided by RSS sources. The RSS source is responsible for what they provide free of charge

# Ending notes

All links belong to us!

