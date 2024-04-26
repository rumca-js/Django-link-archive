Personal link database, link aggregator, with RSS functionality. Similar to Reddit, but completely open source. You can self host it.

It does not capture page contents. It captures link meta data: title, description etc.

# Features

 - local data, no algorithms, no advertisements, self-hosted
 - organize bookmarks, with tags
 - link search functionality. Does not use elastic search
 - maintains website metadata (title, description, thumbnail, etc). It is not [archive.org](https://archive.org) replacement
 - extendable via plugins. RSS feed support. Web page parsing support
 - add personal comments to links
 - supports data import and export. This is most important functionality, as files are more important than the APP itself (file over app strategy)
 - It is not a search engine. Suggesting better alternatives: [whoogle-search](https://github.com/benbusby/whoogle-search), or [Marginalia search](https://search.marginalia.nu/), or [Apache Lucene](https://lucene.apache.org/)
 - Minimal aesthetic. Dark mode, custom list displays

<div align="center">
  <img alt="Django Logo" src="images/django_400.png">
</div>

## Problems with other RSS readers, or apps

 - Most clients are not open source, or are not self-hosted
 - Most RSS clients do not allow manual link input
 - Some programs are not programs from users perspective, but a service: Feedly, Pockets, Readwise Reader. They require account. Their Terms and service can change
 - Most programs fail to provide consistent and exhaustive search ability (NextCloud "News" application, Thunderbird, Feeder Android app, Newsboat Linux app)
 - Most programs do not provide ability to add tag to a link (Thunderbird, Android Feeder app)
 - Scale: Lemmy software is replacement for Reddit, but requires a lot of resources to operate. This project aims to provide "single user" experience
 - Goal: Reddit, Lemmy aim is to provide social media experience, this project aims to grant the ability to create database of links
 - License: Reddit is a nice project, but it is not entirely open source
 - Interface: Most of the RSS programs are GUI: Thunderbird, Feeder. I wanted a server app, that can be accessed from anywhere
 - Import/export. Some programs do not provide any standard to exchange link information, or do not provide any data at all

## Alternatives

Alternative programs exist.

 - [Grimoire](https://github.com/goniszewski/grimoire)
 - [LinkAce](https://www.linkace.org/)
 - [Hoarder](https://hoarder.app/)
 - [GGather](https://web.ggather.com/)
 - [OneKeep](https://onekeep.com/)
 - [Lasso](https://www.lasso.net/go/)
 - [CarryLinks](https://carrylinks.com/)
 - [Zlinky](https://zlinky.com/)
 - [wakelet](https://wakelet.com/)
 - [Booky](https://booky.io/)
 - [Webtag](https://webtag.io/)
 - [Historious](https://historio.us/)
 - [Raindrop](https://raindrop.io/)
 - [Knowies](https://www.knowies.com)

## Possible use cases

 - YouTube filter. You add only your own subscriptions. You can categorize, filter entries from your sources
 - Link aggregator. Similar to Lemmy, Reddit
 - Database of important links: for work, or for school
 - RSS client
 - Data analysis - analyze link rot, how many a page is cited by other sources, analyze link domains

## Suite of projects

 - [Bookmarked links](https://github.com/rumca-js/RSS-Link-Database)
 - [Internet domains, users, projects](https://github.com/rumca-js/Internet-Places-Database)
 - [daily RSS Git repository for the year 2023](https://github.com/rumca-js/RSS-Link-Database-2023)
 - [daily RSS Git repository for the year 2022](https://github.com/rumca-js/RSS-Link-Database-2022)
 - [daily RSS Git repository for the year 2021](https://github.com/rumca-js/RSS-Link-Database-2021)
 - [daily RSS Git repository for the year 2020](https://github.com/rumca-js/RSS-Link-Database-2020)

## Links

 - [Screenshots](https://github.com/rumca-js/Django-link-archive/blob/main/README_ui.md)
 - [Installation, configuration](https://github.com/rumca-js/Django-link-archive/blob/main/README_install.md)
 - [https://renegat0x0.ddns.net/apps/rsshistory/](https://renegat0x0.ddns.net/apps/rsshistory/) - 'news' demo instance. May or may not be runnig actually
 - [https://renegat0x0.ddns.net/apps/catalog/](https://renegat0x0.ddns.net/apps/catalog/) - 'music' demo instance
 - [https://renegat0x0.ddns.net/apps/places/](https://renegat0x0.ddns.net/apps/places/) - 'places' demo instance. Imprtant places
 - [https://renegat0x0.ddns.net/apps/various/](https://renegat0x0.ddns.net/apps/various/) - 'verious' demo instance
 - [Notes about search industry](https://github.com/rumca-js/Django-link-archive/blob/main/README_search.md)
 - [Data analysis](https://github.com/rumca-js/Django-link-archive/blob/main/analysis/readme.md)

# How does it work?

 - First define a RSS source in "Sources" page, or you manually add a link in "Sources" page
 - Every day your bookmarks are exported to a repository, if configured
 - Each new link adds its domain into the 'Domains' pool, if configured
 - Each new link adds words from its title into the 'KeyWords' pool, if configured
 - You can monitor what kinds of domains were added by the links to you system
 - You can monitor what kind of words generate most buzz

# Ranking algorithm

Each page is ranked by several factors.

 - content ranking
 - users votes
 
The result is equal according to calculation
 page ranking = content ranking + users votes

Note: Page rating should not be based 'on time'. Good contents does is not 'worse' because x amount has passed. It should be however a suspect for verification, as it can be a case of abandoned project.

Page rating range is 0..100. This means that if everything is correct for a page, a rank 100 is assigned.

With such approach we can extend page rating and range is still in range 0..100, and it does not break the rest of calculated link rank.

## Content ranking

To have a good page rating, it is desireable to follow good standards:
 - [Open Graph Protocol](https://ogp.me/)
 - [Schema Validator](https://validator.schema.org/)
 - [W3C Validator](https://validator.w3.org/)
 - Provide valid title, which is concise, but not too short
 - Provide valid description, which is concise, but not too short
 - Provide valid publication date
 - Provide valid thumbnail
 - Your page returns valid HTML status code
 - Provide RSS feed
 - Provide search engine keywords tags

The equation for content ranking might change in time, so these rules are pretty vague. It is just better to write good pages.

You may wonder, why am I writing about search engine keywords, if Google does not need them. Well I don't like Google. I would like for other search engines to appear. Such keywords would provide search engine bots to have some idea what the page is about.

## Votes ranking

Database is managed by RSS link database, and user votes. Average of votes is calculated for each link.

# Automatic export

 - Although it archives some data it is not [archive.org](https://archive.org) replacement. It does not automatically store entire pages. It stores meta data about web pages: title, description, thumbnail 
 - Most of views contain "Show JSON" button that provides the view data as JSON. This can be used by scripts, for import, export

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

# Federated

This project is federated. Therefore you can rely on data from other djang-link-archive instances.

You can:
 - define proxy source of automatic import from other link archive instance
 - manually import links from another link archive instance, or

## Proxy sources

First lets define a scenario. You have instance A and instance B. Instance B has defined a source.

You do not want instance A to fetch same data from the internet. You would like to fetch data from instance B.

To do that:
 - Navigate to instance B sources.
 - Find your desired source.
 - Click "Show JSON" (copy location of that address)
 - Navigate on instance A to sources.
 - Add a new source
 - paste the instance B address, the JSON address link
 - the system should suggest source type to be of JSON

## Manual import

Scenario to import sources from a other instance:
 - find sources in the other instance. It should be at "Sources" menu button, by default
 - select which sources you would like to export, you can select a filter
 - click 'Show as JSON', it should produce a nice JSON output
 - copy link URL of that instance, of that JSON output
 - navigate to your instance
 - select 'Admin' page
 - select 'Import from URL', and paste URL

Scenario to import links from a other instance:
 - find links in the other instance. It should be at "Search" menu button, by default
 - select which links you would like to export, you can select a filter, like a date, tag. etc.
 - click 'Show as JSON', it should produce a nice JSON output
 - copy link URL of that instance, of that JSON output
 - navigate to your instance
 - select 'Admin' page
 - select 'Import from URL', and paste URL

# User management [under construction]

Project uses default user auth module.

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

User actions are tracked by the system, only if it is configured so:
 - users can post comments for entries
 - users can tag entries
 - users can vote for entries
 - system stores limited amount of search queries, the user can select previous queries from combobox
 - system stores order of visits on entries. This allows to provide "related" section for each entry. For example if you vist entry "X" after "Y", then "X" will appear on "Y" related section

# Development

Development is described by a separate README: [README_development.md](https://github.com/rumca-js/Django-link-archive/blob/main/README_development.md).

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
 - I do not obtain any form of monetary compensation from link, or data about it. The data link information were already provided by RSS sources. The RSS source is responsible for what they provide free of charge

# Ending notes

All links belong to us!
