import traceback

from ..models import PersistentInfo, LinkDataModel
from ..webtools import Page
from ..dateutils import DateUtils


class BasePlugin(Page):
    def __init__(self, source):
        self.source = source
        super().__init__(self.get_address())
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_address(self):
        return self.source.get_domain()

    def is_link_valid(self, address):
        return True

    def get_link_props(self):
        return []

    def check_for_data(self):
        from ..dateutils import DateUtils

        try:
            source = self.source

            print("process source:{} type:{}".format(source.title, source.source_type))

            if not source.is_fetch_possible():
                print("It is not the right time for source: {}".format(source.title))
                return

            start_time = DateUtils.get_datetime_now_utc()

            num_entries = self.check_for_data_impl(source)

            stop_time = DateUtils.get_datetime_now_utc()
            total_time = stop_time - start_time
            total_time.total_seconds()

            source.set_operational_info(stop_time, num_entries, total_time.total_seconds())

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))

    def check_for_data_impl(self, source):
        try:
            source = self.source

            links_data = self.get_link_props()
            num_entries = len(links_data)

            for link_data in links_data:
                if not link_data:
                    continue

                # print("Adding link {}".format(link_data['link']))
                objs = LinkDataModel.objects.filter(link=link_data['link'])
                if objs.exists():
                    # TODO maybe update with new data?
                    continue

                o = LinkDataModel(
                    source=link_data['source'],
                    title=link_data['title'],
                    description=link_data['description'],
                    link=link_data['link'],
                    date_published=link_data['published'],
                    language=link_data['language'],
                    thumbnail=link_data['thumbnail'],
                    source_obj=source)

                try:
                    o.save()
                    # print("Added link {}".format(link_data['link']))
                except Exception as e:
                    o.save()

            return num_entries

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))