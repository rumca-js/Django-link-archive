import traceback
import hashlib
import base64

from utils.dateutils import DateUtils
from webtoolkit import RemoteServer, ContentLinkParser

from ..webtools import calculate_hash

from ..apps import LinkDatabase
from ..configuration import Configuration
from ..models import AppLogging, UserTags, BaseLinkDataController
from ..controllers import EntryDataBuilder, SourceDataController
from ..controllers import LinkDataController, BackgroundJobController
from ..pluginurl.urlhandler import UrlHandlerEx

from .sourceplugininterface import SourcePluginInterface


class SourceGenericPlugin(SourcePluginInterface):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later

    TODO inherit plugin interface.
    This is "contents" related plugin interface (rss, parse plugins).
    """

    def __init__(self, source_id, options=None):
        super().__init__(source_id, options)
        self.contents = None
        self.content_handler = None
        self.response = None
        self.hash = None

    def check_for_data(self):
        source = self.get_source()
        if not source.enabled:
            return

        # We do not check if data is correct. We can manually add processing to queue
        # We want the source to be processed then

        self.start_time = DateUtils.get_datetime_now_utc()

        self.hash = self.get_hash()

        if source:
            source.update_data()

        if self.is_page_ok_to_read():
            self.read_data_from_container_elements()

        stop_time = DateUtils.get_datetime_now_utc()
        total_time = stop_time - self.start_time
        total_time.total_seconds()

        if self.hash:
            self.set_operational_info(
                stop_time, self.num_read_entries, total_time.total_seconds(), self.hash
            )
            return True

        if self.dead:
            AppLogging.debug(
                "Url:{} Title:{}. Plugin: page is dead".format(source.url, source.title)
            )

            self.set_operational_info(
                stop_time,
                self.num_read_entries,
                total_time.total_seconds(),
                self.hash,
                valid=False,
            )
            return False

    def get_entries(self):
        """
        We override RSS behavior
        """
        self.get_contents()

        c = Configuration.get_object().config_entry

        if c.remote_webtools_server_location:
            if not self.all_properties:
                return calculate_hash("")

            source = self.get_source()

            request_server = RemoteServer(c.remote_webtools_server_location)
            entries = request_server.read_properties_section(
                "Entries", self.all_properties
            )
            if entries is None:
                return []

            for entry in entries:
                entry["date_published"] = DateUtils.parse_datetime(
                    entry["date_published"]
                )
                if source:
                    entry["source"] = source

                    if "language" not in entry or entry["language"] is None:
                        entry["language"] = source.language
                yield entry

    def get_enhanced_entries(self):
        for link_data in self.get_entries():
            if not link_data:
                continue

            if not self.is_link_ok_to_add(link_data):
                AppLogging.error(
                    "Url:{} Title:{}. Cannot add link: {}".format(
                        source.url, source.title, str(link_data)
                    ),
                    stack=True,
                )

                continue

            link_data = self.enhance_properties(link_data)
            yield link_data

    def read_data_from_container_elements(self):
        source = self.get_source()

        for link_data in self.get_enhanced_entries():
            b = EntryDataBuilder()
            entry = b.build(link_data=link_data, source_is_auto=True)

            self.on_added_entry(entry)

            # LinkDatabase.info("Generic plugin item stop:{}".format(link_data["link"]))

    def is_page_ok_to_read(self):
        source = self.get_source()

        if self.hash and source.get_page_hash() == self.hash:
            AppLogging.debug(
                "Url:{} Title:{}. Not changed.".format(source.url, source.title)
            )
            return False
        elif not self.hash:
            AppLogging.debug(
                "Url:{} Title:{}. Cannot obtain hash, skipping ".format(
                    source.url, source.title
                )
            )
            return False

        return True

    def get_hash(self):
        self.get_contents()

        if not self.contents:
            return calculate_hash("")

        c = Configuration.get_object().config_entry
        if c.remote_webtools_server_location:
            if not self.all_properties:
                return calculate_hash("")

            request_server = RemoteServer(c.remote_webtools_server_location)
            response = request_server.read_properties_section(
                "Response", self.all_properties
            )
            encoded_hash = response["body_hash"]
            if not encoded_hash:
                encoded_hash = response["hash"]
            return base64.b64decode(encoded_hash)

    def get_contents(self):
        if self.contents:
            return self.contents

        if self.dead:
            return

        page_link = self.get_address()

        c = Configuration.get_object().config_entry
        if c.remote_webtools_server_location:
            url_ex = UrlHandlerEx(page_link)
            self.all_properties = url_ex.get_properties()

            if not self.all_properties:
                AppLogging.error("Url:{} Could not obtain contents".format(page_link))
                self.dead = True
                return

            contents = url_ex.get_section("Text")
            if contents and "Contents" in contents:
                self.contents = contents["Contents"]
            else:
                self.contents = contents

            if not self.contents:
                AppLogging.error("Url:{} Could not obtain contents".format(page_link))
                self.dead = True
                return

            return self.contents

    def get_address(self):
        source = self.get_source()
        return source.url

    def is_link_valid(self, address):
        return True

    def get_container_elements(self):
        return []

    def add_link(self, link_str):
        tag = ""
        source = self.get_source()
        if source.auto_tag != None and source.auto_tag != "":
            tag = source.auto_tag

        BackgroundJobController.link_add(link_str, source=source, tag=tag)

    def is_link_ok_to_add(self, props):
        if "link" not in props:
            return False
        if props["link"] is None:
            return False
        if props["link"] == "":
            return False

        return True

    def get_links(self):
        """
        Helper function that returns all links found in the source address
        """
        result = []

        c = Configuration.get_object().config_entry
        if not c.accept_non_domain_links and c.accept_domain_links:
            result = self.get_domains()
        elif c.accept_non_domain_links:
            address = self.get_address()

            contents = self.get_contents()
            if not contents:
                return result

            parser = ContentLinkParser(address, contents)

            result = parser.get_links()

        return result

    def get_domains(self):
        """
        Helper function that returns all domains found in the source address
        """
        address = self.get_address()

        contents = self.get_contents()

        if not contents:
            return []

        parser = ContentLinkParser(address, contents)

        result = parser.get_domains()
        return result
