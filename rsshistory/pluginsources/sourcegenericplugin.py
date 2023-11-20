import traceback
import hashlib

from ..models import PersistentInfo
from ..webtools import Page
from ..dateutils import DateUtils
from ..controllers import LinkDataHyperController, SourceDataController
from ..apps import LinkDatabase


class SourceGenericPlugin(Page):
    def __init__(self, source_id):
        self.source_id = source_id
        super().__init__(self.get_address())
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None
        self.hash = None

    def check_for_data(self):
        from ..dateutils import DateUtils

        try:
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

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "[SourceGenericPlugin:check_for_data] Source:{}; Exc:{}\n{}".format(
                    self.source_id, str(e), error_text
                )
            )

    def check_for_data_impl(self):
        try:
            links_data = self.get_link_props()
            num_entries = len(links_data)

            for link_data in links_data:
                if not link_data:
                    continue

                entry = LinkDataHyperController.add_new_link(
                    link_data, source_is_auto=True
                )
                self.on_added_entry(entry)

            return num_entries

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "SourceGenericPlugin:check_for_data_impl: Source:{}; Exc:{}\n{}".format(
                    self.source_id, str(e), error_text
                )
            )

    def is_page_hash_ok(self):
        source = self.get_source()
        self.hash = self.get_hash()

        if self.hash and source.get_page_hash() == self.hash:
            return False

        return True

    def is_fetch_possible(self):
        source = self.get_source()

        print(
            "[{}]: Process source:{} type:{} time:{}".format(
                LinkDatabase.name,
                source.title,
                source.source_type,
                source.get_date_fetched(),
            )
        )

        if not source.is_fetch_possible():
            print(
                "[{}]: Process source:{}: It is not the right time".format(
                    LinkDatabase.name, source.title
                )
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
                print("Exception {}".format(E))

        return self.hash

    def set_operational_info(self, stop_time, num_entries, total_seconds, hash_value):
        source = self.get_source()

        source.set_operational_info(stop_time, num_entries, total_seconds, hash_value)

        print(
            "[{}]: Process source:{} type:{} DONE".format(
                LinkDatabase.name, source.title, source.source_type
            )
        )

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
