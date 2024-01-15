import traceback
import hashlib

from ..models import PersistentInfo
from ..webtools import HtmlPage
from ..dateutils import DateUtils
from ..controllers import LinkDataBuilder, SourceDataController
from ..models import BaseLinkDataController
from ..apps import LinkDatabase


class SourceGenericPlugin(HtmlPage):
    def __init__(self, source_id):
        self.source_id = source_id
        super().__init__(self.get_address())
        self.hash = None

    def check_for_data(self):
        from ..dateutils import DateUtils

        if not self.is_fetch_possible():
            return

        start_time = DateUtils.get_datetime_now_utc()
        num_entries = 0

        if self.is_page_hash_ok():
            num_entries = self.check_for_data_impl()

        stop_time = DateUtils.get_datetime_now_utc()
        total_time = stop_time - start_time
        total_time.total_seconds()

        hash = self.get_hash()
        if hash:
            self.set_operational_info(
                stop_time, num_entries, total_time.total_seconds(), hash
            )

    def check_for_data_impl(self):
        num_entries = 0

        source = self.get_source()

        for link_data in self.get_link_props():
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

                b = LinkDataBuilder()
                b.link_data = link_data
                b.source_is_auto = True

                entry = b.add_from_props()
                if entry:
                    self.on_added_entry(entry)
                    num_entries += 1

        return num_entries

    def is_page_hash_ok(self):
        source = self.get_source()
        self.hash = self.get_hash()

        if self.hash and source.get_page_hash() == self.hash:
            LinkDatabase.info("Page has is the same, skipping".format(source.title))
            return False

        return True

    def is_fetch_possible(self):
        source = self.get_source()

        LinkDatabase.info(
            "Process source:{} type:{} time:{}".format(
                source.title,
                source.source_type,
                source.get_date_fetched(),
            )
        )

        if not source.is_fetch_possible():
            LinkDatabase.info(
                "Process source:{}: It is not the right time".format(source.title)
            )
            return False

        return True

    def get_hash(self):
        if self.hash:
            return self.hash

        text = self.get_contents()
        if text:
            try:
                self.hash = hashlib.md5(text.encode("utf-8")).digest()
            except Exception as E:
                LinkDatabase.info("Could not calculate hash {}".format(E))

        return self.hash

    def set_operational_info(self, stop_time, num_entries, total_seconds, hash_value):
        source = self.get_source()

        source.set_operational_info(stop_time, num_entries, total_seconds, hash_value)

    def get_source(self):
        sources = SourceDataController.objects.filter(id=self.source_id)
        if len(sources) > 0:
            return sources[0]

    def get_address(self):
        source = self.get_source()
        return source.url

    def is_link_valid(self, address):
        return True

    def get_link_props(self):
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
