import traceback
import hashlib

from ..webtools import ContentLinkParser, calculate_hash
from utils.dateutils import DateUtils

from ..apps import LinkDatabase
from ..configuration import Configuration
from ..models import AppLogging, UserTags
from ..models import BaseLinkDataController
from ..controllers import EntryDataBuilder, SourceDataController
from ..controllers import LinkDataController, BackgroundJobController
from ..pluginurl.urlhandler import UrlHandler


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

        AppLogging.debug("Plugin: checking source {}".format(source.url))

        # We do not check if data is correct. We can manually add processing to queue
        # We want the source to be processed then

        start_time = DateUtils.get_datetime_now_utc()
        num_entries = 0

        self.hash = self.calculate_plugin_hash()
        if self.is_page_ok_to_read():
            num_entries = self.read_data_from_container_elements()

        stop_time = DateUtils.get_datetime_now_utc()
        total_time = stop_time - start_time
        total_time.total_seconds()

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

    def read_data_from_container_elements(self):
        num_entries = 0

        start_time = DateUtils.get_datetime_now_utc()
        source = self.get_source()

        for link_data in self.get_entries():
            # LinkDatabase.info("Generic plugin item start:{}".format(link_data["link"]))
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

            if "page_rating" in link_data:
                link_data["page_rating_contents"] = link_data["page_rating"]

            # LinkDatabase.info("Generic plugin item add:{}".format(link_data["link"]))

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
        return self.get_contents_hash()

    def get_contents_hash(self):
        if self.contents:
            return calculate_hash(self.contents)
        return calculate_hash("")

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

        self.content_handler = UrlHandler(self.get_address())
        self.response = self.content_handler.get_response()
        self.contents = self.response.get_text()

        status_code = None
        if self.response:
            status_code = self.response.status_code

        source = self.get_source()

        if not self.response or not self.response.is_valid():
            AppLogging.error(
                info_text="Url:{} Title:{}; Could not obtain contents.".format(
                    source.url,
                    source.title,
                ),
                detail_text="Status code:{}\nOptions:{}\nResponse\n{}".format(
                    status_code,
                    str(self.content_handler.options),
                    self.response,
                ),
            )
            self.dead = True
            return None

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
        if not c.accept_not_domain_entries and c.accept_domains:
            result = self.get_domains()
        elif c.accept_not_domain_entries:
            address = self.get_address()

            u = UrlHandler(address)
            contents = u.get_contents()
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

        u = UrlHandler(address)
        contents = u.get_contents()

        if not contents:
            return []

        parser = ContentLinkParser(address, contents)

        result = parser.get_domains()
        return result
