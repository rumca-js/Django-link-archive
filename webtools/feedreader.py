"""
There is a feedparser, but

a) feedparser does not work with asyncio properly
b) it contained error, which prevented me from reading one RSS feed (it did not read entry.link)
"""

import html
import lxml.etree as ET


__version__ = "0.0.2"


class FeedObject(object):
    def __init__(self, root, ns=None):
        self.root = root
        self.ns = ns

    def get_prop(self, aproperty):
        aproperty_value = self.root.find(aproperty, self.ns)
        if aproperty_value is not None:
            return aproperty_value.text

    def get_prop_attribute(self, aproperty, attribute):
        aproperty_value = self.root.find(aproperty, self.ns)
        if aproperty_value is not None:
            if attribute in aproperty_value.attrib:
                return aproperty_value.attrib[attribute]


class FeedReaderEntry(FeedObject):
    def __init__(self, entry_data, ns):
        super().__init__(entry_data, ns)

        self.link = self.try_to_get_attribute("link", "href")
        self.title = self.try_to_get_field("title")
        self.subtitle = self.try_to_get_field("subtitle")
        self.description = self.try_to_get_field("description")
        if not self.description:
            if "media" in self.ns:
                self.description = self.get_prop(".//media:description")
        if not self.description:
            self.description = self.get_prop("content")
        if not self.description:
            if "atom" in self.ns:
                self.description = self.get_prop("atom:content")

        self.published = self.try_to_get_field("pubDate")
        if not self.published:
            self.published = self.try_to_get_field("published")

        self.media_thumbnail = []

        if "media" in self.ns:
            media_thumbnail = self.get_prop_attribute(".//media:thumbnail", "url")
            if media_thumbnail:
                self.media_thumbnail = [ {"url" : media_thumbnail} ]

        self.media_content = []

        if "media" in self.ns:
            media_content = self.get_prop_attribute(".//media:content", "url")
            if media_content:
                self.media_content = [ {"url" : media_content} ]

        self.author = self.try_to_get_fields("author", "name")

        if not self.author:
            if "itunes" in self.ns:
                self.author = self.get_prop("itunes:owner/itunes:name")

        self.tags = self.try_to_get_field('tags')

    def try_to_get_field(self, field):
        value = self.get_prop("./" + field)
        if not value:
            value = self.get_prop(field)
        if not value:
            if "atom" in self.ns:
                value = self.get_prop(f'atom:{field}')

        return value

    def try_to_get_fields(self, fieldone, fieldtwo):
        value = self.get_prop(f"./{fieldone}/{fieldtwo}")
        if not value:
            value = self.get_prop(f"{fieldone}/{fieldtwo}")
        if not value:
            if "atom" in self.ns:
                value = self.get_prop(f'atom:{fieldone}/atom:{fieldtwo}')

        return value

    def try_to_get_attribute(self, field, attribute):
        value = self.get_prop("./" + field)
        if not value:
            value = self.get_prop_attribute(field, attribute)
        if not value:
            if "atom" in self.ns:
                value = self.get_prop_attribute(f'atom:{field}', attribute)

        return value

    def __contains__(self, item):
        return True


class FeedReaderFeed(FeedObject):
    def __init__(self, root, ns = None, is_atom = False):
        super().__init__(root, ns)

        self.is_atom = is_atom

    def parse(self):
        return self.read()

    def try_to_get_field(self, field):
        value = self.get_prop("./" + field)
        if not value:
            value = self.get_prop(field)
        if not value:
            value = self.get_prop(f'channel/{field}')
        if not value:
            if "atom" in self.ns:
                value = self.get_prop(f'atom:{field}')
        if not field:
            if "atom" in self.ns:
                value = self.get_prop(f'atom:channel/atom:{field}')

        return value

    def try_to_get_fields(self, fieldone, fieldtwo):
        field = self.get_prop(f'./{fieldone}/{fieldtwo}')
        if not field:
            field = self.get_prop(f'{fieldone}/{fieldtwo}')
        if not field:
            if "atom" in self.ns:
                field = self.get_prop(f'./atom:{fieldone}/atom:{fieldtwo}')
        if not field:
            if "atom" in self.ns:
                field = self.get_prop(f'atom:{fieldone}/atom:{fieldtwo}')
        if not field:
            field = self.get_prop(f'./channel/{fieldone}/{fieldtwo}')
        if not field:
            field = self.get_prop(f'channel/{fieldone}/{fieldtwo}')
        if not field:
            if "atom" in self.ns:
                field = self.get_prop(f'./atom:channel/atom:{fieldone}/atom:{fieldtwo}')
        if not field:
            if "atom" in self.ns:
                field = self.get_prop(f'atom:channel/atom:{fieldone}/atom:{fieldtwo}')

        return field

    def try_to_get_attribute(self, field, attribute):
        value = self.get_prop_attribute(field, attribute)
        if not value:
            value = self.get_prop_attribute(f'channel/{field}', attribute)
        if not value:
            if "atom" in self.ns:
                value = self.get_prop_attribute(f'atom:{field}', attribute)
        if not field:
            if "atom" in self.ns:
                value = self.get_prop_attribute(f'atom:channel/atom:{field}', attribute)

        return value

    def read(self):
        self.title = self.try_to_get_field("title")

        self.subtitle = self.try_to_get_field('subtitle')
        self.description = self.try_to_get_field('description')
        self.language = self.try_to_get_field('language')

        self.published = self.try_to_get_field('published')
        if not self.published:
            self.published = self.try_to_get_field('pubDate')
        if not self.published:
            self.published = self.try_to_get_field('lastBuildDate')

        self.author = self.try_to_get_fields('author', 'name')
        if not self.author:
            if "itunes" in self.ns:
                self.author = self.get_prop('.//itunes:author')
        if not self.author:
            if "itunes" in self.ns:
                self.author = self.get_prop('itunes:author')
        if not self.author:
            if "itunes" in self.ns:
                self.author = self.get_prop('./channel/itunes:author')
        if not self.author:
            if "atom" in self.ns and "itunes" in self.ns:
                self.author = self.get_prop('./atom:channel/itunes:author')

        self.tags = self.try_to_get_field('tags')

        image = {}
        image["url"] = self.try_to_get_fields("image","url")
        if not image["url"]:
            image["url"] = self.try_to_get_attribute("image", "url")
        image["href"] = self.try_to_get_fields("image","href")
        if not image["href"]:
            if "atom" in self.ns:
                image["href"] = self.try_to_get_attribute("image", "href")
        image["width"] = self.try_to_get_fields("image", "width")
        image["height"] = self.try_to_get_fields("image", "height")
        self.image = image

    def __contains__(self, item):
        return True


class FeedReader(object):
    def __init__(self, contents):
        self.contents = contents.strip()
        if self.contents.strip().startswith("<html"):
            self.process_html()

        self.entries = []
        self.ns = self.get_namespaces()
        self.root = None

        self.title = None

    def parse(contents):
        r = FeedReader(contents)
        r.parse_implementation()
        return r

    def parse_implementation(self):
        if not self.contents:
            return

        parser = ET.XMLParser(strip_cdata=False)
        self.root = ET.fromstring(self.contents.encode(), parser=parser)

        is_atom = "atom" in self.ns

        self.feed = FeedReaderFeed(self.root, ns = self.ns, is_atom= is_atom)
        self.feed.parse()

        entries = self.get_entries()
        if not entries:
            entries = self.get_items()

        self.read_entries(entries)

    def get_namespaces(self):
        spaces = {}

        wh = 0
        while wh != -1:
            xmlns_wh = self.contents.find("xmlns", wh)
            if xmlns_wh == -1:
                break
            xmlns_comma_wh = self.contents.find(":", xmlns_wh)
            if xmlns_comma_wh == -1:
                break
            xmlns_eq_wh = self.contents.find("=", xmlns_wh)
            if xmlns_eq_wh == -1:
                break
            xmlns_quote1_wh = self.contents.find('"', xmlns_eq_wh)
            if xmlns_quote1_wh == -1:
                break
            xmlns_quote2_wh = self.contents.find('"', xmlns_quote1_wh + 1)
            if xmlns_quote2_wh == -1:
                break

            if xmlns_comma_wh > xmlns_eq_wh:
                ns = ""
            else:
                ns = self.contents[xmlns_comma_wh+1 : xmlns_eq_wh]
            link = self.contents[xmlns_quote1_wh+1: xmlns_quote2_wh]

            spaces[ns] = link

            wh = xmlns_quote2_wh + 1

        return spaces

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

    def read_entries(self, entries):
        for entry in entries:
            self.entries.append(FeedReaderEntry(entry, self.ns))

    def get_entries(self):
        entries = self.root.findall('.//entry', self.ns)
        if len(entries) > 0:
            return entries

        if "atom" in self.ns:
            entries = self.root.findall('.//atom:entry', self.ns)
            if len(entries) > 0:
                return entries

    def get_items(self):
        entries = self.root.findall('.//item', self.ns)
        if len(entries) > 0:
            return entries

        if "atom" in self.ns:
            entries = self.root.findall('.//atom:item', self.ns)
            if len(entries) > 0:
                return entries
