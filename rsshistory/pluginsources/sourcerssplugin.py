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

    def get_link_props(self):
        c = Configuration.get_object().config_entry

        contents = self.get_contents()
        source = self.get_source()

        fast_check = False

        if not self.is_rss(fast_check=fast_check):
            PersistentInfo.error(
                "Source:{} Title:{}; Not RSS.\nStatus code:{}\nContents\n{}".format(
                    source.url, source.title, self.status_code, contents
                )
            )

            if self.is_cloudflare_protected():
                LinkDatabase.info(
                    "Source:{} Title:{}; Feed is protected by Cloudflare".format(
                        source.url, source.title, self.status_code, contents
                    )
                )

            # goes over cloudflare
            self.reader = UrlHandler.get(
                self.get_address(), use_selenium=True, fast_check=fast_check
            )
            contents = self.reader.get_contents()

            if not self.reader.is_rss(fast_check=fast_check):
                """
                Sometimes RSS might hide in <body>. I know that is stupid.
                Parse the HTML with BeautifulSoup.
                """
                soup = BeautifulSoup(contents, "html.parser")
                body_find = soup.find("body")
                if not body_find:
                    PersistentInfo.error(
                        "Source:{} Title:{}; Cannot process source, not RSS.\nStatus code:{}\nContents\n{}".format(
                            source.url, source.title, self.reader.status_code, contents
                        )
                    )
                    return None

                rss_contents = body_find.get_text()

                self.reader = RssPage(self.get_address(), contents=rss_contents)

                if not self.reader.is_rss(fast_check=fast_check):
                    PersistentInfo.error(
                        "Source:{} Title:{}; Cannot process source, not RSS.\nStatus code:{}\nContents\n{}".format(
                            source.url, source.title, self.reader.status_code, contents
                        )
                    )

                return None
            else:
                PersistentInfo.create(
                    "Source:{} Title:{}; Successfull workaround for Cloudlare.".format(
                        source.url, source.title
                    )
                )

        self.reader = RssPage(self.get_address(), contents=contents)
        all_props = self.reader.parse_and_process()

        num_entries = len(all_props)

        if num_entries == 0:
            if source and contents:
                PersistentInfo.error(
                    "Source:{} Title:{}; Source page has no data {}".format(
                        source.url, source.title, contents
                    )
                )
                return None
            elif not contents:
                PersistentInfo.error(
                    "Source:{} Title:{}; could not obtain page".format(
                        source.url, source.title
                    )
                )
                return None
            else:
                PersistentInfo.error(
                    "Source:{}; Source has no data".format(self.source_id)
                )
                return None

        for index, prop in enumerate(all_props):
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
                    "Rss plugin link:{} [{}/{}]".format(
                        prop["link"], index, num_entries
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
