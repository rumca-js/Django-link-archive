# Overview

Some time ago I have started capturing links from RSS sources. Why? I am not sure. I was just enjoying development in Django. I am no expert, but I like to program stuff.

 - Django application to manage RSS sources
 - Allows to add/remove RSS sources
 - Each source adds entries to the database

## Features

 - Web GUI in Django
 - RSS feed sources management: adding / removing / configuration
 - RSS links managment: adding / removing / configuration
 - automatic RSS feed update
 - automatic git export
 - automatic cleanup after specified time
 - making some entries permament (not erasable, highlighted)
 - support for Django auth staff users
 - automatic behavior through threads, which I think are not a good solution for Django applications?

## Links

 - Django RSS application: [https://github.com/rumca-js/Django-rss-feed](https://github.com/rumca-js/Django-rss-feed)
 - Git RSS daily repository for the year 2022 [https://github.com/rumca-js/RSS-Link-Database-2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - Git RSS links repository for the permament articles [https://github.com/rumca-js/RSS-Link-Database](https://github.com/rumca-js/RSS-Link-Database)

## Screenshots

![](https://raw.githubusercontent.com/rumca-js/Django-rss-feed/main/screenshots/2022_09_14_entries.PNG)

## Installation

Installation, just as any other Django app.

## Dependencies

 - sudo apt install feedparser / pip3 install feedparser
 - pip3 install python-dateutil
 - pip3 install PyGithub

## Daily repository

 - repository for a particular year contains directories for each day
 - each day contains files for each source
 - there is markdown and json file for each source

## Permament repository

 - contains articles that I have selected as intresting, or noteworthy, or funny, or whathever
 - files are split by 'language' and 'year' categories
 - three file formats: JSON, markdown, rss
 - markdown file is generated as a form of preview, JSON can be reused, imported
 - links are highlighted, but that does not necessarily mean something is endorsed. It shows particular intrest in topic. It is indication of importance

## Sources

 - provided in sources.json file
 - provides information about sources, like title, url, langugage

## Goal

 - Archive purposes
 - data analysis - probably it would be possible to verify link rot, etc.
 - I want to have a place to store important links
 - Google sucks at providing results for various topics (dead internet)

## Inspirations

 - I Tracked Everything I Read on the Internet for a Year [https://www.tdpain.net/blog/a-year-of-reading](https://www.tdpain.net/blog/a-year-of-reading).
 - Automating a Reading List [https://zanshin.net/2022/09/11/automating-a-reading-list/](https://zanshin.net/2022/09/11/automating-a-reading-list/)
 - Google Search Is Dying [https://dkb.io/post/google-search-is-dying](https://dkb.io/post/google-search-is-dying)
 - Luke Smith: Remember to Consoom Next Content on YouTube [https://www.youtube.com/watch?v=nI3GVw2JSEI](https://www.youtube.com/watch?v=nI3GVw2JSEI). As a society we provide news instead of building a data base of important information
 - Bright Insight: YES, They Really Are Deleting the Internet And it’s WAY Worse Than You Think [https://www.youtube.com/watch?v=8O_NvPpbsbw](https://www.youtube.com/watch?v=8O_NvPpbsbw). Data are removed from 'visibility' in Google and other platforms.

Reasoning in Polish:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/QHBcLrlgaxY/0.jpg)](https://www.youtube.com/watch?v=QHBcLrlgaxY)

## Data analysis

With these data we can perform further analysis:

 - how many of old links are not any longer valid (link rot test)
 - capture all domains from RSS links (internal, and leading outside?). Analyse which domains are most common
 - which site generates most entries
 - we can capture all external links from entries, to capture where these sites lead to (check network effect, etc)
 - we can verify who reported first on certain topics

## Problems, notes

 - Google fails to deliver content of small creators (blogs etc. private pages). Google focuses on corporate hosting. Most common links are towards YouTube, Google maps, Facebook, reddit
 - We cannot replace Google search
 - Google provides only 31 pages of news (in news filter) and around 10 pages for ordinary search. This is a very small number. It is like looking through keyhole at the Internet
 - Link rot is real. My links may be not working after some time
 - Is the data relevant, or useful for anyone?
 - Either we would like to record data from 'well established sources' or gather as many links as possible. I think web engines do it? We cannot gather too much data, as it can destroy our potato servers.
 - there are other RSS solutions like 'feedly', but it is an app, not data. You cannot parse it, you do not own the data, you can only do things that feedly allows you to do

# Ending notes

All links belong to us!
