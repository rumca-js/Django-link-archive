import traceback
import hashlib
import base64

from ..webtools import ContentLinkParser, calculate_hash, RemoteServer
from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..configuration import Configuration
from ..models import AppLogging, UserTags
from ..models import BaseLinkDataController
from ..controllers import EntryDataBuilder, SourceDataController
from ..controllers import LinkDataController, BackgroundJobController
from ..pluginurl.urlhandler import UrlHandlerEx


class SourceGenericPlugin(object):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """

    def __init__(self, source_id, options=None):
        self.source_id = source_id
        self.source = None
        self.contents = None
        self.content_handler = None
        self.response = None
        self.dead = False

        self.get_source()

        self.hash = None

    def check_for_data(self):
        source = self.get_source()
        if not source.enabled:
            return

        print("Starting processing source:{}".format(source.url))

        # We do not check if data is correct. We can manually add processing to queue
        # We want the source to be processed then

        start_time = DateUtils.get_datetime_now_utc()
        num_entries = 0

        self.hash = self.calculate_plugin_hash()

        if source:
            source.update_data()

        if self.is_page_ok_to_read():
            num_entries = self.read_data_from_container_elements()

        stop_time = DateUtils.get_datetime_now_utc()
        total_time = stop_time - start_time
        total_time.total_seconds()

        print("Stopping processing source:{}".format(source.url))

        if self.hash:
            self.set_operational_info(
                stop_time, num_entries, total_time.total_seconds(), self.hash
            )
            return True

        if self.dead:
            AppLogging.debug(
                "Url:{} Title:{}. Plugin: page is dead".format(source.url, source.title)
            )

            self.set_operational_info(
                stop_time,
                num_entries,
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

            request_server = RemoteServer(c.remote_webtools_server_location)
            entries = request_server.read_properties_section(
                "Entries", self.all_properties
            )
            for entry in entries:
                entry["date_published"] = DateUtils.parse_datetime(
                    entry["date_published"]
                )
                entry["source"] = self
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
        num_entries = 0

        start_time = DateUtils.get_datetime_now_utc()
        source = self.get_source()

        for link_data in self.get_enhanced_entries():
            b = EntryDataBuilder()
            b.link_data = link_data
            b.source_is_auto = True

            entry = b.build_from_props()

            # AppLogging.debug("Url:{} Title:{}. Generic plugin add:{} DONE".format(source.url, source.title, link_data["link"]))

            # TODO should below be in data builder?

            if entry and entry.date_published > start_time:
                if source.auto_tag:
                    user = Configuration.get_object().get_superuser()
                    UserTags.set_tags(entry, source.auto_tag, user)

                self.on_added_entry(entry)
                num_entries += 1

            # LinkDatabase.info("Generic plugin item stop:{}".format(link_data["link"]))

        return num_entries

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]

    def enhance_properties(self, properties):
        source = self.get_source()

        if source:
            if (
                self.is_property_set(properties, "language")
                and source.language != None
                and source.language != ""
            ):
                properties["language"] = source.language

            properties["source_url"] = source.url
            properties["source"] = source
            if source.age > 0:
                properties["age"] = source.age

        if "page_rating" in properties:
            properties["page_rating_contents"] = properties["page_rating"]

        return properties

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

    def calculate_plugin_hash(self):
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

    def set_operational_info(
        self, stop_time, num_entries, total_seconds, hash_value, valid=True
    ):
        source = self.get_source()

        source.set_operational_info(
            stop_time, num_entries, total_seconds, hash_value, valid
        )

    def get_source(self):
        if self.source is None:
            sources = SourceDataController.objects.filter(id=self.source_id)
            if sources.count() > 0:
                self.source = sources[0]

        return self.source

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

    def on_added_entry(self, entry):
        """
        TO be implemented
        """
        pass

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
