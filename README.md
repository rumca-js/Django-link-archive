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

# Goal

 - Archive purposes
 - I want to 'store important links'
 - Google sucks at providing results for various topics (dead internet)

## Inspirations

 - I Tracked Everything I Read on the Internet for a Year [https://www.tdpain.net/blog/a-year-of-reading](https://www.tdpain.net/blog/a-year-of-reading).
 - Automating a Reading List [https://zanshin.net/2022/09/11/automating-a-reading-list/](https://zanshin.net/2022/09/11/automating-a-reading-list/)
 - Google Search Is Dying [https://dkb.io/post/google-search-is-dying](https://dkb.io/post/google-search-is-dying)
 - Luke Smith: Remember to Consoom Next Content on YouTube [https://www.youtube.com/watch?v=nI3GVw2JSEI](https://www.youtube.com/watch?v=nI3GVw2JSEI). As a society we provide news instead of building a data base of important information
 - Bright Insight: YES, They Really Are Deleting the Internet And it’s WAY Worse Than You Think [https://www.youtube.com/watch?v=8O_NvPpbsbw](https://www.youtube.com/watch?v=8O_NvPpbsbw). Data are removed from 'visibility' in Google and other platforms.

Reasoning in Polish:

[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/QHBcLrlgaxY/0.jpg)](https://www.youtube.com/watch?v=QHBcLrlgaxY)

# Problems, notes

 - Google fails to deliver content of small creators (blogs etc. private pages). Google focuses on corporate hosting. Most common links are towards YouTube, Google maps, Facebook, reddit
 - We cannot replace Google search
 - Google provides only 31 pages of news (in news filter) and around 10 pages for ordinary search. This is a very small number. It is like looking through keyhole at the Internet
 - Link rot is real. My links may be not working after some time
 - Is the data relevant, or useful for anyone?
 - Either we would like to record data from 'well established sources' or gather as many links as possible. I think web engines do it? We cannot gather too much data, as it can destroy our potato servers.
 - there are other RSS solutions like 'feedly', but it is an app, not data. You cannot parse it, you do not own the data, you can only do things that feedly allows you to do
