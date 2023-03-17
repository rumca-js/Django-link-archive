Link database, with RSS functionality

# Features

 - Web GUI in Django
 - Local data, no algorithms, no advertisments
 - Search ability (Google like), by language, author, tags
 - Ability to provide custom plugins, parse HTML pages
 - Can be used in a NAS device
 - RSS feed sources management: adding / removing / configuration
 - RSS links managment: adding / removing / configuration
 - RSS links managment: bookmark support, tag support
 - Minimal aestethic: no distraction, compact layout
 - automatic / configurable RSS feed update
 - automatic / configurable git export

## Problems with other RSS readers

 - Currently Nextcloud 'News' plugin does not provide: tag support, search ability
 - Thunderbird does not allow tagging, searching links by tags
 - Feedly is not local, does not store your data on your hardware
 - Feeder (phone) does not provide search ability, nor tagging. Cannot configure 'view' for my liking
 - Newsboat is CLI, and it does not provide exhaustive search capabilities

## Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2023_03_09_entries.PNG)

## Notes

 - it is best to use on a device with SSD

## Installation

Installation, just as any other Django app. Link [https://docs.djangoproject.com/en/4.1/intro/tutorial01/](https://docs.djangoproject.com/en/4.1/intro/tutorial01/).

## Dependencies

 - sudo apt install feedparser / pip3 install feedparser
 - pip3 install python-dateutil

## Suite of projects

 - Captured using Django application: [https://github.com/rumca-js/Django-rss-feed](https://github.com/rumca-js/Django-rss-feed)
 - daily RSS Git repository for the year 2022 [https://github.com/rumca-js/RSS-Link-Database-2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - daily RSS Git repository for the year 2023 [https://github.com/rumca-js/RSS-Link-Database-2023](https://github.com/rumca-js/RSS-Link-Database-2023)
 - Bookmarked links [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)

## Goal

 - I want to 'store important links'
 - Archive purposes
 - Data analysis - possible to verify link rot, etc.
 - Google sucks at providing results for various topics (dead internet)

## Inspirations

 - I Tracked Everything I Read on the Internet for a Year [https://www.tdpain.net/blog/a-year-of-reading](https://www.tdpain.net/blog/a-year-of-reading).
 - Automating a Reading List [https://zanshin.net/2022/09/11/automating-a-reading-list/](https://zanshin.net/2022/09/11/automating-a-reading-list/)
 - Google Search Is Dying [https://dkb.io/post/google-search-is-dying](https://dkb.io/post/google-search-is-dying)
 - Luke Smith: Search Engines are Totally Useless Now... [https://www.youtube.com/watch?v=N8P6MTOQlyk](https://www.youtube.com/watch?v=N8P6MTOQlyk)
 - Luke Smith: Remember to Consoom Next Content on YouTube [https://www.youtube.com/watch?v=nI3GVw2JSEI](https://www.youtube.com/watch?v=nI3GVw2JSEI). As a society we provide news instead of building a data base of important information
 - Ryan George What Google Search Is Like In 2022 [https://www.youtube.com/watch?v=NT7_SxJ3oSI](https://www.youtube.com/watch?v=NT7_SxJ3oSI)

# Data

## Bookmarks

 - contains articles that I have selected as intresting, or noteworthy, or funny, or whathever
 - files are split by 'language' and 'year' categories
 - three file formats: JSON, markdown, rss
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
 - Internet Archive (archive.org) does not provide snapshots for each and every day for all RSS sources. It is sometimes pretty slow. We would like to be sure that a such snapshot takes place. Therefore we need to export links to daily repo ourselves. Django RSS app also makes requests to archive to make the snapshots
 - It is hard to define which sources are to be added into database. Even though I have more than 100 sources, I check regularly only a handful of them
 - there are other RSS solutions like 'feedly', but it is an app, not data. You cannot parse it, you do not own the data, you can only do things that feedly allows you to do

# Ending notes

All links belong to us!

