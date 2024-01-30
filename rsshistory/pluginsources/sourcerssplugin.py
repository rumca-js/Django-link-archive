import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..models import PersistentInfo
from ..apps import LinkDatabase
from ..webtools import RssPage, Url
from ..pluginentries.entryurlinterface import EntryUrlInterface
from ..configuration import Configuration
from ..pluginentries.entryurlinterface import UrlHandler

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

        fast_check = False

        if self.is_cloudflare_protected() or not contents or not self.is_rss(fast_check=fast_check):
            if self.options.is_selenium():
                self.store_error(source, "Tried with selenium, still not RSS", contents)
                self.dead = True
                return

            # goes over cloudflare
            self.reader = UrlHandler.get(
                self.get_address(), use_selenium=True, fast_check=fast_check
            )
            contents = self.reader.get_contents()
            self.status_code = self.reader.status_code

            if not self.reader.is_rss(fast_check=fast_check):
                """
                Sometimes RSS might hide in <body>. I know that is stupid.
                Parse the HTML with BeautifulSoup.
                """
                if not contents:
                    self.store_error(source, "Coult not obtain contents, even with selenium", contents)
                    self.dead = True
                    return None

                soup = BeautifulSoup(contents, "html.parser")
                body_find = soup.find("body")
                if not body_find:
                    self.store_error(source, "No HTML body in page", contents)
                    self.dead = True
                    return None

                rss_contents = body_find.get_text()

                self.reader = RssPage(self.get_address(), contents=rss_contents)

                if not self.reader.is_rss(fast_check=fast_check):
                    self.store_error(source, "HTML body does not provide RSS", contents)
                    self.dead = True

                    return None
                else:
                    contents = rss_contents
            else:
                PersistentInfo.create(
                    "Source:{} Title:{}; Successfull workaround for Cloudlare.".format(
                        source.url, source.title
                    )
                )

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
            if "link" not in prop:
                continue

            prop = self.cleanup_data(prop)

            if self.is_link_ok_to_add(prop):
                if c.auto_store_entries_use_clean_page_info:
                    print("RSS: use clean page info")
                    prop = self.get_clean_page_info(prop)

                elif c.auto_store_entries_use_all_data:
                    print("RSS: use updated page info")
                    prop = self.get_updated_page_info(prop)

                prop = self.enhance(prop)

                LinkDatabase.info(
                    "Rss plugin link:{} [{}]".format(
                        prop["link"], index
                    )
                )
                yield prop

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
