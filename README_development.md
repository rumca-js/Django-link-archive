# Hardware requirements

The goal is to create personal archive database. We require small footprint.
It should be able to operate on SBC, like raspberry PI.

# On web scraping

Please do not make anyone live miserable. It was designed to capture information from publicly available data (for example RSS), not to exploit anybody.

On the other hand some web pages use sofisticated barriers that prevents us from successfuly scraping the web contents.

Most common techniques:
 - Some pages do not display contents, or provide invalid html data. You can use different user agent. Best results can be obtained if we used chrome user agent
 - Spotify does not display any HTML code if we use common python requests API. For such pages we can use "selenium"
 - Web page uses cloudflare and checks if you are human. There are several techniques for that. There is chromium stealth and other solutions

RSS reading is not easy: [https://flak.tedunangst.com/post/cloudflare-and-rss](https://flak.tedunangst.com/post/cloudflare-and-rss)

That gives us the conslusion, you have to be a sneaky bot, even if what you are doing is not wrong.

# Keep it small

We want small footprint. The database cannot grow indefinitely.

Keep limits on user actions:
 - store up to preconfigured amount of data. Searches might be store for a user, but we store only about 100 searches. Newer replace older
 - store data only for links that are in the operational database. If links leave operational database, so are data related to it: comments, votes
 - always define archive limit
 - always define amount of days when entries are removed

# Development

 - installation should be simple and easy. Provide most common installation methods (Python poetry, docker)
 - limit barriers of entry. There should be no obstacles
 - easy import and exported data. The user need to be able to create a new instance in a matter of minutes
 - default configuration should cover 90% of needs
 - KISS. Do not focus on javascript, and other libraries that make the project bloated, hard to develop for

# Conventions

 - everything that relates to link should start with "Entry"
 - everything that relates to source should start with "Source"
 - new services are handled by 'services' directory (like handling GIT, webarchive, etc.)
 - handling of new sites might require changes in pluginsources, and pluginentries (the first handles source, the second one a entry, link)
 - this program was not designed to store Internet pages, but to store Internet meta data (title, description). We should rely on other services for cooperation. We cannot store entire Internet on a hard drive. We can store some meta though

# Design

 - all links are stored in LinkDataModel. Links older than the configured period are moved to archive table.

## Notes

 - do not change exported names of link data model. We do not want to be forced to regenerate all links again. We can add new fields though
 - do not fetch all objects from any table. Do not use Model.objects.all(). One exception: to obtain length of table
 - do not use len() for checking length of table. Use queryset 'count' API
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
