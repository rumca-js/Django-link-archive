

import feedparser

url = 'https://tvn24.pl/najnowsze.xml'
feed = feedparser.parse(url)

print(feed.feed)
print(feed.feed.title)
print(feed.entries)

for entry in feed.entries:
    print(entry)
    print()
    print(entry.title)
    print()
    print(entry.description)
    print()
    print(entry.link)
    print()
    print(entry.published)
    print()
