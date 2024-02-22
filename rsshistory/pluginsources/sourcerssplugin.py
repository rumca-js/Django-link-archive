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
    """
    TODO this inherits HTML, not RSS
    """

    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source_id):
        print("BaseRssPlugin:constr0")
        super().__init__(source_id)
        source = self.get_source()
        print("BaseRssPlugin:constr1:{}".format(source.url))

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
            h = HtmlPage(self.get_address(), page_object=self)
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
                source.url, source.title, self.status_code, text, print_contents[:self.get_contents_size_limit()]
            )
        )

    def get_contents_size_limit(self):
        return 400

    def get_container_elements(self):
        """
        We override RSS behavior
        """
        c = Configuration.get_object().config_entry

        contents = self.get_contents()
        source = self.get_source()

        if not contents:
            return

        self.reader = RssPage(self.get_address(), page_object=self)
        all_props = self.reader.get_container_elements()

        for index, prop in enumerate(all_props):
            # LinkDatabase.info("Processing RSS element")
            if "link" not in prop:
                continue

            prop = self.enhance(prop)

            if self.is_link_ok_to_add(prop):
                yield prop
            # LinkDatabase.info("Processing RSS element DONE")
        # LinkDatabase.info("Processing RSS elements DONE")

    def enhance(self, prop):
        if prop["link"].endswith("/"):
            prop["link"] = prop["link"][:-1]
        return prop

    def calculate_plugin_hash(self):
        """
        We do not care about RSS title changing. We care only about entries
        Generic handler uses Html as base. We need to use RSS for body hash
        """
        self.get_contents()
        reader = RssPage(self.get_address(), page_object=self)
        return reader.get_body_hash()
