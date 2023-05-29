Link database, with RSS functionality. Similar to Reddit, but completly open source, on your local machine.

# Features

 - Local data, no algorithms, no advertisments
 - Web GUI, accessible from anywhere (LAN, public, however it is configured)
 - Search ability (Google-like), by language, author, tags
 - Ability to extend, to provide custom plugins, parse HTML pages
 - RSS feed support (RSS sources)
 - Sources management: adding, removing, configuration
 - Link managment: manual adding, removing, configuration, bookmark support, tag support, admin user comments
 - Minimal aestethic: no distraction, compact layout
 - Configurable: lists, timeouts
 - Automatic git export, RSS source import
 - Minimal installation, integrator may choose however to use production environment, with a good Database engine. Just as it is supported by Django. I am using SQLite without any problems.
 - Support for web archive. Link rot mitigation

## Problems with other RSS readers

 - Currently Nextcloud 'News' plugin does not provide: tag support, search ability
 - Thunderbird does not allow tagging, searching links by tags
 - Feedly is not local, does not store your data on your hardware
 - Feeder (phone) does not provide search ability, nor tagging. Cannot configure 'view' for my liking
 - Newsboat is CLI, and it does not provide exhaustive search capabilities
 - Most do not allow to introduce my own links
 - Fail to provide consistent search ability

## Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2023_03_09_entries.PNG)

View screenshots: [https://github.com/rumca-js/Django-rss-feed/tree/main/screenshots](https://github.com/rumca-js/Django-rss-feed/tree/main/screenshots).

## Notes

 - it is best to use on a device with SSD

## Installation

Installation, just as any other Django app. Link [https://docs.djangoproject.com/en/4.1/intro/tutorial01/](https://docs.djangoproject.com/en/4.1/intro/tutorial01/).

## Dependencies

 - sudo apt install feedparser / pip3 install feedparser
 - pip3 install python-dateutil

## Suite of projects

 - Captured using Django application: [https://github.com/rumca-js/Django-rss-feed](https://github.com/rumca-js/Django-rss-feed)
 - Bookmarked links [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)
 - daily RSS Git repository for the year 2023 [https://github.com/rumca-js/RSS-Link-Database-2023](https://github.com/rumca-js/RSS-Link-Database-2023)
 - daily RSS Git repository for the year 2022 [https://github.com/rumca-js/RSS-Link-Database-2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - daily RSS Git repository for the year 2021 [https://github.com/rumca-js/RSS-Link-Database-2021](https://github.com/rumca-js/RSS-Link-Database-2021)
 - daily RSS Git repository for the year 2020 [https://github.com/rumca-js/RSS-Link-Database-2020](https://github.com/rumca-js/RSS-Link-Database-2020)

## Goal

 - Archive. I want to 'store important links'
 - Data analysis - possible to verify link rot, etc.
 - Google sucks at providing results for various topics (dead internet)

Development:

 - KISS. Project should be of small footprint
 - It should be small, easy to setup
 - I did not focus on supporting multiple users, it is designed currently on small scale projects

## Inspirations

 - I Tracked Everything I Read on the Internet for a Year [https://www.tdpain.net/blog/a-year-of-reading](https://www.tdpain.net/blog/a-year-of-reading).
 - Automating a Reading List [https://zanshin.net/2022/09/11/automating-a-reading-list/](https://zanshin.net/2022/09/11/automating-a-reading-list/)
 - Google Search Is Dying [https://dkb.io/post/google-search-is-dying](https://dkb.io/post/google-search-is-dying)
 - Luke Smith: Search Engines are Totally Useless Now... [https://www.youtube.com/watch?v=N8P6MTOQlyk](https://www.youtube.com/watch?v=N8P6MTOQlyk)
 - Luke Smith: Remember to Consoom Next Content on YouTube [https://www.youtube.com/watch?v=nI3GVw2JSEI](https://www.youtube.com/watch?v=nI3GVw2JSEI). As a society we provide news instead of building a data base of important information
 - Ryan George What Google Search Is Like In 2022 [https://www.youtube.com/watch?v=NT7_SxJ3oSI](https://www.youtube.com/watch?v=NT7_SxJ3oSI)

# Data

Program is able to store bookmarked links, and links for each day.

Each day has it's own directory. Therefore it is easy to regenerate data for a particular day, without disturbing other data.

## Bookmarks

 - three file formats: JSON, markdown, rss
 - contains articles that I have selected as intresting, or noteworthy, or funny, or whathever
 - files are split by 'language' and 'year' categories
 - markdown file is generated as a form of preview, JSON can be reused, imported
 - links are highlighted, but that does not necessarily mean something is endorsed. It shows particular intrest in topic. It is indication of importance
 
## Daily Data

 - RSS links are captured for each source separately
 - two files formats for each day and source: JSON and markdown
 - markdown file is generated as a form of preview, JSON can be reused, imported
 - links are bookmarked, but that does not necessarily mean something is endorsed. It shows particular intrest in topic. It is indication of importance. Such links are stored 'forever'

## Sources

 - provided in sources.json file
 - provides information about sources, like title, url, langugage

## Data analysis

With these data we can perform further analysis:

 - how many of old links are not any longer valid (link rot test)
 - capture all domains from RSS links (internal, and leading outside?). Analyse which domains are most common
 - which site generates most entries
 - we can capture all external links from entries, to capture where these sites lead to (check network effect, etc)
 - we can verify who reported first on certain topics

# Problems, notes

 - Google fails to deliver content of small creators (blogs etc. private pages). Google focuses on corporate hosting, or deliver products that make investors happy. Most common links are towards YouTube, Google maps, Facebook, Reddit
 - We cannot replace Google search, since I do not have processing power for that. For programming problems I still go to Google, to find specific information
 - Google provides only 31 pages of news (in news filter) and around 10 pages for ordinary search. This is a very small number. It is like looking through keyhole at the Internet
 - This link database, with more than 100 of sources provides many useful data. For example after searching for 'covid' in links I have thounsands of results, just as I would expect
 - Dead Internet is not a problem for me, since I do not capture data from bot farms
 - Some topics are so popular, that all of the sources write about it, and I am swamped with links about recent crisises
 - Even though I have 100 sources, I still find useful info from outside of my sources. Some through YouTube, some through Reddit, etc.
 - Link rot is real. Some of archived links may be not working after some time. This is especially true for msn, and yahoo, which quite fast delete older links from their database
 - It is hard to define which sources are to be added into database. Even though I have more than 100 sources, I check regularly only a handful of them

I could not decide if my link database should be public or not. Therefore I created two environments:
 - public, with all important information
 - private, with links that are not relevant for the public

## Analysis of Tools

Archive.org:
 - Is not reliable. Sometimes it gets painfully slow. It is still better than nothing
 - Most mainstream media RSS is covered, but the coverage is spotty. Not all days are covered
 - Internet Archive (archive.org) does not provide snapshots for each and every day for all RSS sources. It is sometimes pretty slow. We would like to be sure that a such snapshot takes place. Therefore we need to export links to daily repo ourselves. Django RSS app also makes requests to archive to make the snapshots

RSS tools:
 - Some do not provide ability to bookmark entries
 - Some do not provide ability to add tags entries (useful for searching entries with a particular tag)
 - Some do not provide ability to search for a particular title, etc. Searching mechanisms are limiting
 - There is no ability to fetch archived data. I have been using archive.org to import historic RSS data, but not all data are available
 - Some of RSS tools are not local (feedly), which for me is a problem

## Legal

 - I do not endorse any link every link in the database. I may some links be important because of how bad the content is. I use irony often, therefore beware!
 - Everyone has a right to be forgotten. If any link should be removed from a database please contact me
 - I do not obtain any form of monetary recompensation from link, or data about it. The data link information were already provided by RSS sources. The RSS source is responsible for what they provide free of charge

# Ending notes

All links belong to us!

