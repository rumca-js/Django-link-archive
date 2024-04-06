import traceback
import hashlib

from ..models import AppLogging
from ..webtools import HtmlPage, PageOptions, ContentLinkParser, calculate_hash
from ..dateutils import DateUtils
from ..controllers import LinkDataBuilder, SourceDataController
from ..controllers import LinkDataController
from ..configuration import Configuration
from ..models import BaseLinkDataController
from ..apps import LinkDatabase
from ..pluginurl.urlhandler import UrlHandler, UrlPropertyValidator


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
        self.response = None
        self.dead = False

        source = self.get_source()

        if source:
            options = UrlHandler.get_url_options(source.url)

        self.hash = None

    def check_for_data(self):
        source = self.get_source()
        if not source.enabled:
            return

        LinkDatabase.info("Plugin: checking source {}".format(source.url))

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
            LinkDatabase.info("Plugin: page is dead {}".format(self.get_source().url))

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

        for link_data in self.get_container_elements():
            # LinkDatabase.info("Generic plugin item start:{}".format(link_data["link"]))
            if not link_data:
                continue

            if "link" not in link_data or not link_data["link"]:
                AppLogging.error(
                    "Invalid link properties. Missing key: {}".format(str(link_data))
                )

                continue

            if source:
                link_data["source"] = source.url
                link_data["source_obj"] = source
                if source.age > 0:
                    link_data["age"] = source.age

            if "page_rating" in link_data:
                link_data["page_rating_contents"] = link_data["page_rating"]

            # LinkDatabase.info("Generic plugin item add:{}".format(link_data["link"]))

            b = LinkDataBuilder()
            b.link_data = link_data
            b.source_is_auto = True

            entry = b.add_from_props()

            LinkDatabase.info(
                "Generic plugin add:{} DONE".format(link_data["link"])
            )

            if entry and entry.date_published > start_time:
                self.on_added_entry(entry)
                num_entries += 1

            # LinkDatabase.info("Generic plugin item stop:{}".format(link_data["link"]))

        return num_entries

    def is_page_ok_to_read(self):
        source = self.get_source()

        if self.hash and source.get_page_hash() == self.hash:
            LinkDatabase.info(
                "Page not changed: {} {}".format(source.url, source.title)
            )
            return False
        elif not self.hash:
            LinkDatabase.info(
                "Cannot obtain hash, skipping {} {}".format(source.url, source.title)
            )
            return False

        return True

    def is_fetch_possible(self):
        source = self.get_source()

        if not source.is_fetch_possible():
            return False

        return True

    def calculate_plugin_hash(self):
        self.get_contents()
        return self.get_contents_hash()

    def get_contents_hash(self):
        return calculate_hash(self.contents)

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

        handler = UrlHandler(self.get_address())
        contents = handler.get_contents()
        self.response = handler.response
        status_code = None
        if self.response:
            status_code = self.response.status_code

        source = self.get_source()

        if not contents:
            AppLogging.error(
                "Source:{} Title:{}; Could not obtain contents.\nStatus code:{}\nContents\n{}".format(
                    source.url, source.title, status_code, contents
                )
            )
            self.dead = True
            return None

        self.contents = contents

        return contents

    def get_address(self):
        source = self.get_source()
        return source.url

    def is_link_valid(self, address):
        return True

    def get_container_elements(self):
        return []

    def on_added_entry(self, entry):
        """
        TO be implemented
        """
        pass

    def is_link_ok_to_add(self, props):
        try:
            is_archive = BaseLinkDataController.is_archive_by_date(
                props["date_published"]
            )
            if is_archive:
                # LinkDatabase.info("Link is for archive")
                return False

            objs = LinkDataController.objects.filter(link=props["link"])

            if not objs.exists():
                if "title" not in props:
                    AppLogging.error(
                        "Link:{}; Title:{} missing published field".format(
                            props["link"],
                            props["title"],
                        )
                    )
                    return False

                if not self.is_link_valid(props["link"]):
                    LinkDatabase.info("Link is not valid")
                    return False

                if "date_published" not in props:
                    AppLogging.error(
                        "Link:{}; Title:{} missing published field".format(
                            props["link"],
                            props["title"],
                        )
                    )
                    return False

                return True

            return False

        except Exception as e:
            error_text = traceback.format_exc()
            if props and "link" in props and "title" in props:
                AppLogging.error(
                    "Link:{}; Title:{}; Exc:{}\n{}".format(
                        props["link"],
                        props["title"],
                        str(e),
                        error_text,
                    )
                )

            return None

    def get_links(self):
        """
        Helper function that returns all links found in the source address
        """
        result = []

        c = Configuration.get_object().config_entry
        if not c.auto_store_entries and c.auto_store_domain_info:
            result = self.get_domains()
        elif c.auto_store_entries:
            address = self.get_address()

            u = UrlHandler(address)
            contents = u.get_contents()

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

        parser = ContentLinkParser(address, contents)

        result = parser.get_domains()
        return result
