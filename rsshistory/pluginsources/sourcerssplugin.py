import traceback
from dateutil import parser
from bs4 import BeautifulSoup

from ..models import AppLogging
from ..apps import LinkDatabase
from ..webtools import RssPage, HtmlPage
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

        url = self.get_address()

        p = RssPage(url, contents)
        if p.is_valid():
            self.contents = p.get_contents()
            return self.contents

        p = HtmlPage(url, contents)
        if p.is_valid():
            rss_contents = p.get_body_text()

            self.reader = RssPage(self.get_address(), contents=rss_contents)

            if not self.reader.is_valid():
                self.store_error(
                    source, "HTML body does not provide RSS, body", rss_contents
                )
                self.dead = True

                return None
            else:
                contents = rss_contents
                self.contents = p.get_contents()
                return contents

        self.store_error(source, "Page does not provide RSS", contents)
        self.dead = True

        return None

        self.contents = contents

        return contents

    def store_error(self, source, text, contents):
        if contents:
            print_contents = contents
        else:
            print_contents = "None"

        status_code = None
        if self.response:
            status_code = self.response.status_code

        AppLogging.error(
            "Source:{}\nTitle:{}\nStatus code:{}\nText:{}.\nContents\n{}".format(
                source.url,
                source.title,
                status_code,
                text,
                print_contents[: self.get_contents_size_limit()],
            )
        )

    def get_contents_size_limit(self):
        return 800

    def get_container_elements(self):
        """
        We override RSS behavior
        """
        c = Configuration.get_object().config_entry

        contents = self.get_contents()
        source = self.get_source()

        if not contents:
            return

        self.reader = RssPage(self.get_address(), contents)
        all_props = self.reader.get_container_elements()

        for index, prop in enumerate(all_props):
            if "link" not in prop:
                LinkDatabase.info(
                    "Link not present in RSS:{}".format(self.get_address())
                )
                continue

            prop = self.enhance(prop)

            if self.is_link_ok_to_add(prop):
                yield prop
            # LinkDatabase.info("Processing RSS element DONE")
        # LinkDatabase.info("Processing RSS elements DONE")

    def enhance(self, prop):
        if prop["link"].endswith("/"):
            prop["link"] = prop["link"][:-1]

        source = self.get_source()

        if (
            self.is_property_set(prop, "language")
            and source.language != None
            and source.language != ""
        ):
            prop["language"] = source.language

        return prop

    def calculate_plugin_hash(self):
        """
        We do not care about RSS title changing. We care only about entries
        Generic handler uses Html as base. We need to use RSS for body hash
        """
        contents = self.get_contents()
        reader = RssPage(self.get_address(), contents)
        return reader.get_body_hash()

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
