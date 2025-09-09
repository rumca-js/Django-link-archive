# Howdy partner! So you want to become sheriff?

You can be one.

# Hardware requirements

 - the application is optimized for low-resource environments
 - must run reliably on SBC devices like the Raspberry Pi 5

# Storage & Footprint

 - We aim to keep the database small and controlled:
 - The archive must not grow indefinitely.
 - Users should only store essential data.
 - Archiving limits must be defined and enforced.
 - Avoid storing entire webpages — only metadata like title and description.

# Naming & Directory Conventions

 - Entry*: Refers to links or individual items.
 - Source*: Refers to content sources (e.g., RSS feeds).
 - Services like Git or Web Archive go in the services/ directory.
 - Data serialization logic lives in the serializers/ directory.
 - We use a limited amount of job queues.
 - This system is not a full web archive — it complements other tools by storing metadata only.

# Ethical Crawling Guidelines

 - This project was designed to interact with publicly accessible content responsibly.
 - Respect robots.txt.
 - Avoid aggressive crawling — use reasonable intervals.
 - Don't burden sites or break terms of service.
 - Prefer RSS or open APIs when possible.

# Common Crawling Challenges

 - Some websites hide content unless accessed with a browser-like User-Agent.
 - Services like Spotify block Python HTTP libraries — consider using Selenium.
 - Cloudflare and other services use bot-detection (use tools like Chromium Stealth).
 - In short: Even ethical bots sometimes need to be "sneaky."

Cloudflare and RSS [https://flak.tedunangst.com/post/cloudflare-and-rss](https://flak.tedunangst.com/post/cloudflare-and-rss)

# Development

 - Easy installation: Support Poetry and Docker.
 - Minimal configuration: Defaults should satisfy 90% of users.
 - Clean UX: User actions should be simple and intuitive.
 - Modular tasks: Offload heavy lifting to queues/jobs.
 - Easy data import/export.
 - REST-like APIs: Frontend does most of the processing.
 - Include useful defaults: RSS sources, block lists, etc.
 - Keep It Simple (KISS).

# Crawling architecture

Parts:
 - django application
 - crawling server (cralwer buddy)
 - queue background thread
 
# Code & DB Practices

 - Avoid changing exported names in the Link model.
 - Never use .all() unless necessary. Use .count() only when measuring length.
 - Prefer .exists() over .count() for existence checks.
 - Use timezone.now() instead of datetime.now().
 - Process large datasets in batches, not via .all().
 - For SQLite: Avoid high-concurrency. Cache or pass values instead of querying frequently.
 - Keep in mind parts of code, or architectural ideas are moved to other repos, so make the code reusable
 
# Reserved names

Some usernames and tags have predefined meanings. [TBD]

Some tags will have special meaning. These tags might be used to produce dashboards, etc.

Tags:
 - gatekeepers
 - search engine
 - social platform
