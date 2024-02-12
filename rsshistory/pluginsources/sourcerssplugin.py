import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..models import PersistentInfo
from ..apps import LinkDatabase
from ..webtools import RssPage, Url, HtmlPage
from ..pluginurl.entryurlinterface import EntryUrlInterface, UrlHandler
from ..configuration import Configuration

from .sourcegenericplugin import SourceGenericPlugin


class BaseRssPlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_contents(self):
        if self.contents:
            return self.contents

        if self.dead:
            return

        source = self.get_source()

        contents = super().get_contents()

        if not contents:
            self.store_error(
                source,
                "Coult not obtain contents, even with selenium",
                contents,
            )
            self.dead = True
            return

        fast_check = False

        if self.is_html(fast_check=fast_check):
            h = HtmlPage(self.get_address(), page_object = self)
            rss_contents = h.get_body_text()

            self.reader = RssPage(self.get_address(), contents=rss_contents)

            if not self.reader.is_rss(fast_check=fast_check):
                self.store_error(source, "HTML body does not provide RSS", contents)
                self.dead = True

                return None
            else:
                contents = rss_contents

        self.contents = contents

        return contents

    def store_error(self, source, text, contents):
        if contents:
            print_contents = contents
        else:
            print_contents = "None"

        PersistentInfo.error(
            "Source:{}\nTitle:{}\nStatus code:{}\nText:{}.\nContents\n{}".format(
                source.url, source.title, self.status_code, text, print_contents[:300]
            )
        )

    def get_container_elements(self):
        c = Configuration.get_object().config_entry

        contents = self.get_contents()
        source = self.get_source()

        if not contents:
            return

        self.reader = RssPage(self.get_address(), contents=contents)
        all_props = self.reader.get_container_elements()

        for index, prop in enumerate(all_props):
            #LinkDatabase.info("Processing RSS element")
            if "link" not in prop:
                continue

            prop = self.cleanup_data(prop)

            if self.is_link_ok_to_add(prop):
                if c.auto_store_entries_use_clean_page_info:
                    prop = self.get_clean_page_info(prop)

                elif c.auto_store_entries_use_all_data:
                    prop = self.get_updated_page_info(prop)

                prop = self.enhance(prop)

                yield prop
            #LinkDatabase.info("Processing RSS element DONE")
        #LinkDatabase.info("Processing RSS elements DONE")

    def cleanup_data(self, prop):
        if prop["link"].endswith("/"):
            prop["link"] = prop["link"][:-1]
        return prop

    def get_clean_page_info(self, prop):
        i = EntryUrlInterface(prop["link"])
        new_props = i.get_props()
        if not new_props:
            return prop

        for key in new_props:
            if new_props[key] is not None:
                prop[key] = new_props[key]
        return prop

    def get_updated_page_info(self, prop):
        i = EntryUrlInterface(prop["link"])
        new_props = i.get_props(prop)
        return prop

    def enhance(self, prop):
        prop = self.cleanup_data(prop)

        source = self.get_source()

        if source:
            prop["source"] = source.url
            if "language" not in prop:
                prop["language"] = source.language
            if "artist" not in prop:
                prop["artist"] = source.title
            if "album" not in prop:
                prop["album"] = source.title
        else:
            prop["source"] = self.reader.url
            if "language" not in prop:
                prop["language"] = self.reader.get_language()
            if "artist" not in prop:
                prop["artist"] = self.reader.get_artist()

        return prop

    def calculate_plugin_hash(self):
        """
        We do not care about RSS title changing. We care only about entries
        Generic handler uses Html as base. We need to use RSS for body hash
        """
        p = RssPage(self.get_address(), page_object = self)
        return p.get_body_hash()
