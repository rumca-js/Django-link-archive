"""
There is a feedparser, but

a) feedparser does not work with asyncio properly
b) it contained error, which prevented me from reading one RSS feed (it did not read entry.link)
"""

import html
from xml.etree import ElementTree


__version__ = "0.0.1"


class FeedObject(object):
    def __init__(self, root):
        self.root = root
        self.ns = {'atom': 'http://www.w3.org/2005/Atom', "media" : "http://search.yahoo.com/mrss/"}

    def get_prop(self, aproperty):
        aproperty_value = self.root.find(aproperty, self.ns)
        if aproperty_value is not None:
            return aproperty_value.text

    def get_prop_attribute(self, aproperty, attribute):
        aproperty_value = self.root.find(aproperty, self.ns)
        if aproperty_value is not None:
            if attribute in aproperty_value.attrib:
                return aproperty_value.attrib[attribute]


class FeedReaderAtomEntry(FeedObject):
    def __init__(self, entry_data):
        super().__init__(entry_data)

        self.link = self.get_prop_attribute("atom:link", "href")
        if not self.link:
            self.link = self.get_prop("atom:link")

        self.title = self.get_prop("atom:title")
        self.description = self.get_prop(".//media:description")
        if not self.description:
            self.description = self.get_prop("atom:content")

        self.published = self.get_prop("atom:pubDate")
        if not self.published:
            self.published = self.get_prop("atom:published")

        self.media_thumbnail = []

        media_thumbnail = self.get_prop_attribute(".//media:thumbnail", "url")
        if media_thumbnail:
            self.media_thumbnail = [ {"url" : media_thumbnail} ]

        self.media_content = []

        media_content = self.get_prop_attribute(".//media:content", "url")
        if media_content:
            self.media_content = [ {"url" : media_content} ]

        self.author = self.get_prop("atom:author/atom:name")

        self.tags = self.get_prop('atom:tags')

    def __contains__(self, item):
        return True


class FeedReaderRssEntry(FeedObject):
    def __init__(self, entry_data):
        super().__init__(entry_data)

        self.link = self.get_prop_attribute("link", "href")
        if not self.link:
            self.link = self.get_prop("link")

        self.title = self.get_prop("title")
        self.description = self.get_prop("description")
        if not self.description:
            self.description = self.get_prop("content")

        self.published = self.get_prop("pubDate")
        if not self.published:
            self.published = self.get_prop("published")

        self.media_thumbnail = []

        media_thumbnail = self.get_prop_attribute(".//thumbnail", "url")
        if media_thumbnail:
            self.media_thumbnail = [ {"url" : media_thumbnail} ]

        self.media_content = []

        media_content = self.get_prop_attribute(".//content", "url")
        if media_content:
            self.media_content = [ {"url" : media_content} ]

        self.author = self.get_prop("author/name")

        self.tags = self.get_prop('tags')

    def __contains__(self, item):
        return True


class FeedReaderFeed(FeedObject):
    def __init__(self, root, is_atom = False, is_rss = False):
        super().__init__(root)

        self.is_atom = is_atom
        self.is_rss = is_rss

    def parse(self):
        if self.is_atom:
            return self.read_atom()
        if self.is_rss:
            return self.read_rss()

    def read_atom(self):
        self.title = self.get_prop('atom:title')
        self.subtitle = self.get_prop('atom:subtitle')
        self.description = self.get_prop('atom:description')
        self.language = self.get_prop('atom:language')
        self.published = self.get_prop('atom:published')
        if not self.published:
            self.published = self.get_prop('atom:pubDate')
        self.author = self.get_prop('atom:author/atom:name')
        self.tags = self.get_prop('atom:tags')

        self.image = self.get_prop_attribute("atom:image", "href")
        if not self.image:
            self.image = self.get_prop_attribute("atom:image", "url")

    def read_rss(self):
        self.title = self.get_prop('title')
        self.subtitle = self.get_prop('subtitle')
        self.description = self.get_prop('description')
        self.language = self.get_prop('language')
        self.published = self.get_prop('published')
        if not self.published:
            self.published = self.get_prop('pubDate')
        self.author = self.get_prop('author/name')
        self.tags = self.get_prop('tags')

        self.image = self.get_prop_attribute("image", "href")
        if not self.image:
            self.image = self.get_prop_attribute("image", "url")

    def __contains__(self, item):
        return True


class FeedReader(object):
    def __init__(self, contents):
        self.contents = contents
        if self.contents.strip().startswith("<html"):
            self.process_html()

        self.entries = []
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}
        self.root = None
        self.title = None

    def process_html(self):
        wh = self.contents.find("&lt;")
        if wh == -1:
            self.contents = None
            return False

        last_wh = self.contents.rfind("&gt;")
        if last_wh == -1:
            self.contents = None
            return False

        # +4 to compensate for &gt; text
        self.contents = self.contents[wh: last_wh + 4]
        self.contents = html.unescape(self.contents)

        return True

    def read_entries_atom(self):
        entries = self.root.findall('.//atom:entry', self.ns)
        # print(f"entries: {entries}")
        for entry in entries:
            self.entries.append(FeedReaderAtomEntry(entry))

    def read_entries_rss(self):
        # parse the RSS feed using xml.etree.ElementTree
        entries = self.root.findall('.//item', self.ns)
        for entry in entries:
            self.entries.append(FeedReaderRssEntry(entry))

    def parse(contents):
        r = FeedReader(contents)
        r.parse_implementation()
        return r

    def parse_implementation(self):
        if not self.contents:
            return

        self.root = ElementTree.fromstring(self.contents)

        self.feed = FeedReaderFeed(self.root, is_atom = self.is_atom(), is_rss = self.is_rss())
        self.feed.parse()

        if self.is_atom():
            self.read_entries_atom()
        elif self.is_rss():
            self.read_entries_rss()

    def is_atom(self):
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = self.root.findall('.//atom:entry', self.ns)
        return len(entries) > 0

    def is_rss(self):
        self.ns = {'atom': 'http://www.w3.org/2005/Atom'}
        entries = self.root.findall('.//item', self.ns)
        return len(entries) > 0
