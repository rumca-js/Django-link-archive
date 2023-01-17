# Features

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
 - Nextcloud 'News' plugin however currently does not provide: tag support, search ability
 - thunderbird does not allow tagging, searching by tags
 - feedly is not local, does not store your data on your hardware
 - feeder does not provide search ability, nor tagging. Does not display icons for RSS entries, in views
 - newsboat is CLI, and it does not provide exhaustive search capabilities

## Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2023_01_13_entries.PNG)

## Notes

 - Web GUI in Django
 - it is best to use on a device with SSD

## Installation

Installation, just as any other Django app.

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

 - Internet Archive (archive.org) does not provide snapshots for each and every day for all RSS sources. It is sometimes pretty slow. We would like to be sure that a such snapshot takes place. Therefore we need to export links to daily repo ourselves. Django RSS app also makes requests to archive to make the snapshots
 - Google fails to deliver content of small creators (blogs etc. private pages). Google focuses on corporate hosting. Most common links are towards YouTube, Google maps, Facebook, reddit
 - We cannot replace Google search
 - Google provides only 31 pages of news (in news filter) and around 10 pages for ordinary search. This is a very small number. It is like looking through keyhole at the Internet
 - Link rot is real. My links may be not working after some time
 - Is the data relevant, or useful for anyone?
 - Either we would like to record data from 'well established sources' or gather as many links as possible. I think web engines do it? We cannot gather too much data, as it can destroy our potato servers.
 - there are other RSS solutions like 'feedly', but it is an app, not data. You cannot parse it, you do not own the data, you can only do things that feedly allows you to do

# Ending notes

All links belong to us!

