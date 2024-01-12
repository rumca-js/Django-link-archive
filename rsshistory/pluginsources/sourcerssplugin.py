import traceback
from dateutil import parser

from ..models import PersistentInfo
from ..apps import LinkDatabase
from ..webtools import RssPage

from .sourcegenericplugin import SourceGenericPlugin
from ..pluginentries.entryurlinterface import EntryUrlInterface


class BaseRssPlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)

    def get_link_props(self):
        from ..configuration import Configuration

        c = Configuration.get_object().config_entry

        self.reader = RssPage(self.get_address(), self.get_contents())
        all_props = self.reader.parse_and_process()

        num_entries = len(all_props)

        if num_entries == 0:
            source = self.get_source()

            if source:
                PersistentInfo.error(
                    "Source:{}/{}; Source has no data".format(source.url, source.title)
                )
            else:
                PersistentInfo.error(
                    "Source:{}; Source has no data".format(self.source_id)
                )

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
