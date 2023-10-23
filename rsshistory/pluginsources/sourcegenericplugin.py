import traceback

from ..models import PersistentInfo
from ..webtools import Page
from ..dateutils import DateUtils
from ..controllers import LinkDataHyperController
from ..apps import LinkDatabase


class SourceGenericPlugin(Page):
    def __init__(self, source):
        self.source = source
        super().__init__(self.get_address())
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_address(self):
        return self.source.url

    def is_link_valid(self, address):
        return True

    def get_link_props(self):
        return []

    def on_added_entry(self, entry):
        pass

    def check_for_data(self):
        from ..dateutils import DateUtils

        try:
            source = self.source

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
                return

            start_time = DateUtils.get_datetime_now_utc()

            num_entries = self.check_for_data_impl(source)

            stop_time = DateUtils.get_datetime_now_utc()
            total_time = stop_time - start_time
            total_time.total_seconds()

            source.set_operational_info(
                stop_time, num_entries, total_time.total_seconds()
            )

            print(
                "[{}]: Process source:{} type:{} DONE".format(
                    LinkDatabase.name, source.title, source.source_type
                )
            )

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "[SourceGenericPlugin:check_for_data] Source:{} {}; Exc:{}\n{}".format(
                    source.url, source.title, str(e), error_text
                )
            )

    def check_for_data_impl(self, source):
        try:
            source = self.source

            links_data = self.get_link_props()
            num_entries = len(links_data)

            for link_data in links_data:
                if not link_data:
                    continue

                entry = LinkDataHyperController.add_new_link(link_data)
                self.on_added_entry(entry)

            return num_entries

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "SourceGenericPlugin:check_for_data_impl: Source:{} {}; Exc:{}\n{}".format(
                    source.url, source.title, str(e), error_text
                )
            )
