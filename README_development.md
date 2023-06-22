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

 - Everything that relates to link should start with "Entry"
 - Everything that relates to source should start with "Source"
 - New services are handled by 'services' directory
 - Handling of new sites might require changes in pluginsources, and pluginentries (the first handles source, the second one a entry, link)

## Notes

 - do not fetch all objects from any table. Do not use Model.objects.all(). One exception: to obtain length of table
