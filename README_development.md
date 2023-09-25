# Hardware requirements

The goal is to create personal archive database. We require small footprint.
It should be able to operate on SBC, like raspberry PI.

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

# Design

 - all links are stored in LinkDataModel. Links older than the configured period are moved to archive table.

## Notes

 - do not change exported names of link data model. We do not want to be forced to regenerate all links again. We can add new fields though
 - do not fetch all objects from any table. Do not use Model.objects.all(). One exception: to obtain length of table
 - do not use len() for checking length of table. Use queryset 'count' API
 - do not use datetime.now(). Use django timezone datetime, or other native means
 
# Omni search

Uses sympy.

Processing:
 - read input condition from input to symbol equation that can be digested by sympy 
      * (link_field = search_value) into (A) condition
      * (link_field = search_value) & (link_field2 = search_value2) into (A) & (B) condition
 - traverse with sympy equation
 - translate each condition (A, B ...) into Django Q objects
 - use Q object to select from link database
