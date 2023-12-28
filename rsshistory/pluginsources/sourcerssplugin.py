import traceback
from dateutil import parser

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo, BaseLinkDataController
from ..apps import LinkDatabase


class BaseRssPlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source_id):
        super().__init__(source_id)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_link_props(self):
        from ..webtools import RssPage

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
            prop = self.enhance(prop)
            if self.is_link_ok_to_add(prop):
                LinkDatabase.info(
                    "Rss plugin link:{} [{}/{}]".format(
                        prop["link"], index, num_entries
                    )
                )
                yield prop

    def enhance(self, prop):
        if prop["link"].endswith("/"):
            prop["link"] = prop["link"][:-1]

        source = self.get_source()

        if source:
            prop["source"] = source.url
            prop["language"] = source.language
            prop["artist"] = source.title
            prop["album"] = source.title
        else:
            RssPage
            prop["source"] = self.reader.url
            prop["language"] = self.reader.get_language()
            prop["artist"] = self.reader.get_artist()

        return prop
