import traceback
import hashlib

from ..models import PersistentInfo
from ..webtools import HtmlPage, PageOptions
from ..dateutils import DateUtils
from ..controllers import LinkDataBuilder, SourceDataController
from ..models import BaseLinkDataController
from ..apps import LinkDatabase
from ..pluginurl.urlhandler import UrlHandler


class SourceGenericPlugin(HtmlPage):
    """
    Class names schemes:
     - those that are ancestors, and generic use "Base" class prefix
     - file names start with source, because I did not know if they will not be in one place
       with entries, so I wanted to be able to distinguish them later
    """

    def __init__(self, source_id, options=None):
        self.source_id = source_id
        self.source = None

        source = self.get_source()
        if source:
            options = UrlHandler.get_url_options(source.url)

        super().__init__(self.get_address(), options=options)

        self.hash = None

    def check_for_data(self):
        source = self.get_source()
        LinkDatabase.info("Plugin: checking source {}".format(source.url))

        if not self.is_fetch_possible():
            LinkDatabase.info(
                "Plugin source:{}: It is not the right time for update".format(
                    source.title
                )
            )
            return

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
                PersistentInfo.error(
                    "Invalid link properties. Missing key: {}".format(str(link_data))
                )
            else:
                if source:
                    link_data["source"] = source.url
                    link_data["source_obj"] = source

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

        contents = super().get_contents()

        source = self.get_source()

        fast_check = False

        if self.is_cloudflare_protected() or not contents:
            LinkDatabase.info(
                "Source:{} Title:{}; Feed is protected by Cloudflare".format(
                    source.url, source.title, self.status_code, contents
                )
            )

            if self.options.is_selenium():
                self.dead = True
                return

            # goes over cloudflare
            self.reader = UrlHandler.get(
                self.get_address(), use_selenium=True, fast_check=fast_check
            )
            contents = self.reader.get_contents()

            if not contents:
                PersistentInfo.error(
                    "Source:{} Title:{}; Could not obtain contents.\nStatus code:{}\nContents\n{}".format(
                        source.url, source.title, self.reader.status_code, contents
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
            from ..controllers import LinkDataController

            is_archive = BaseLinkDataController.is_archive_by_date(
                props["date_published"]
            )
            if is_archive:
                # LinkDatabase.info("Link is for archive")
                return False

            objs = LinkDataController.objects.filter(link=props["link"])

            if not objs.exists():
                if "title" not in props:
                    PersistentInfo.error(
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
                    PersistentInfo.error(
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
                PersistentInfo.error(
                    "Link:{}; Title:{}; Exc:{}\n{}".format(
                        props["link"],
                        props["title"],
                        str(e),
                        error_text,
                    )
                )

            return None
