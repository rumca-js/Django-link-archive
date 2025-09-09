# Howdy partner! So you want to become sheriff?

You can be one.

# Hardware requirements

The goal is to create personal archive database. We require small footprint. It should be able to run on SBC, like raspberry PI 5.

# Keep it small

We want small footprint. The database cannot grow indefinitely.

Keep limits on user actions:
 - store data only necessary amount of data
 - always define archive limit, we do not allow the database to grow indefinitely

# Conventions

 - everything that relates to link should start with "Entry"
 - everything that relates to source should start with "Source"
 - new services are handled by 'services' directory (like handling GIT, webarchive, etc.)
 - serialization is handled by 'serializers' directory
 - we use one queue to check for jobs, and processing queue. We do not need many queues, as it makes system more difficult. We do not need speed, as we are ethical scrapers
 - this program was not designed to store Internet pages, but to store Internet meta data (title, description). We should rely on other services for cooperation. We cannot store entire Internet on a hard drive. We can store some meta though

# On web crawling

Please do not make anyone live miserable. It was designed to capture information from publicly available data (for example RSS), not to exploit anybody.

We should not crawling aggressively. Reads intervals should be sane. We should be reading robots.txt

On the other hand some web pages use sofisticated barriers that prevents us from successfuly crawling the web contents.

Most common techniques:
 - Some pages do not display contents, or provide invalid html data. You can use different user agent. Best results can be obtained if we used chrome user agent
 - Spotify does not display any HTML code if we use common python requests API. For such pages we can use "selenium"
 - Web page uses cloudflare and checks if you are human. There are several techniques for that. There is chromium stealth and other solutions

RSS reading is not easy: [https://flak.tedunangst.com/post/cloudflare-and-rss](https://flak.tedunangst.com/post/cloudflare-and-rss)

That gives us the conslusion, you have to be a sneaky bot, even if what you are doing is not wrong.

# On RSS buttons 'mark all read'
The button is stupid because it is not true. When you have RSS reader it fetches links into the database. When you hit the button, you did not in fact read all.

 - The software marks user visits, which can be interpreted as 'reading'. When you visit RSS entry it counts as a 'read'
 - You cannot click one button and mark everything as 'read'
 - User visits mark database row. If we have 500 RSS sources, we can have many many links. To limit footprint we do not want visit for all links in database to be generated
 - We can think about a button that marks point in time, that everything "before" is not new. Maybe we can think about "mark all read" to be consistent with other software, but it will be using something underneat that marks a border between what's new

# Development

 - installation should be simple and easy. Provide most common installation methods (Python poetry, docker)
 - user interactions should be short and simple. Move some code to tasks, jobs, queues
 - limit barriers of entry. There should be no obstacles for user. Software should be ready to be used from start
 - easy import and exported data. The user need to be able to create a new instance in a matter of minutes
 - default configuration should cover 90% of needs
 - KISS
 - use REST-like API, so that browser on client side does heavy lifting
 - provide initial data. Add some RSS sources, block lists, or any other things, that help user to start the project

# Crawling algorithm

Parts:
 - django application
 - crawling server (script_server.py)
 - crawling script (for example crawleebeautifulsoup.py)

Scenario:
 - Django app detects it needs meta data
 - Connects to crawling server, sends request
 - crawling server starts script
 - crawling script tries to obtain info about link, returns data to crawling server
 - crawling server sends data back to caller (django app)

## Notes

 - do not change exported names of link data model. We do not want to be forced to regenerate all links again. We can add new fields though
 - do not fetch all objects from any table. Do not use Model.objects.all(). One exception: to obtain length of table
 - do not use len() for checking length of table. Use queryset 'count' API
 - do not use count() if exists() is enough
 - do not use datetime.now(). Use django timezone datetime, or other native means
 - do not iterate over object using .all() [Use batch approach](https://djangosnippets.org/snippets/1170/)
 - if SQLlite is used, then try to cache data. Requesting many things from database might lead to database locking. Therefore passing objects as arguments may not necessarily be the best idea
 
# Omni search

Uses sympy.

Processing:
 - read input condition from input to symbol equation that can be digested by sympy 
      * (link_field = search_value) into (A) condition
      * (link_field = search_value) & (link_field2 = search_value2) into (A) & (B) condition
 - traverse with sympy equation
 - translate each condition (A, B ...) into Django Q objects
 - use Q object to select from link database

# Styles

Most of views use 'lists' to display elements.

Each link element style is reflected by a separate style in a CSS file.

What if we do not want to use main style for highlights, but for youtube we would like a slightly different color?

Each style should be independent from other styles.

# Reserved names

Expect some names to be reserved.

Users:
 - OpenPageRank - this user will be used to add votes from page rank

Some tags will have special meaning. These tags might be used to produce dashboards, etc.

Tags:
 - gatekeepers
 - search engine
 - social platform

# Debugging and other calls

Celery can be debugged as follows
```
celery --help
celery inspect --help
celery call --help
```

Shows which tasks are running
```
poetry run celery inspect registered
```

Call process jobs with JSON arguments
```
celery call app.tasks.process_all_jobs -a '["rsshistory.threadhandlers.OneTaskProcessor"]'
```
