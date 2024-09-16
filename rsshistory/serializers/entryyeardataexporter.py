import logging
import shutil
from django.contrib.auth.models import User
from django.db.models import Q

import datetime

from utils.dateutils import DateUtils

from ..models import AppLogging, UserBookmarks, UserTags
from ..apps import LinkDatabase
from ..controllers import LinkDataController
from utils.serializers.converters import (
    ModelCollectionConverter,
    JsonConverter,
    MarkDownDynamicConverter,
    RssConverter,
)
from .entriesexporter import MainExporter, EntriesExporter


class EntryYearDataExporter(EntriesExporter):
    def __init__(self, data_writer_config, entries):
        super().__init__(data_writer_config, entries)

    def items2mdtext(self, items, source_url=None):
        column_order = ["title", "link", "date_published", "tags", "date_dead_since"]
        md = MarkDownDynamicConverter(items, column_order)
        md_text = md.export()

        return md_text


class EntryYearDataMainExporter(MainExporter):
    def __init__(self, data_writer_config, user=None):
        super().__init__(data_writer_config, user=user)

    def get_start_year(self):
        """
        We export from oldest entries
        """
        entries = LinkDataController.objects.all().order_by("date_published")

        if len(entries) > 0:
            entry = entries[0]
            if entry.date_published:
                str_date = entry.date_published.strftime("%Y")
                try:
                    return int(str_date)
                except Exception as E:
                    LinkDatabase.info("Error: {}".format(str(E)))

        return self.get_current_year()

    def get_current_year(self):
        today = DateUtils.get_date_today()
        year = int(DateUtils.get_datetime_year(today))
        return year

    def export(self, directory):
        entries_dir = directory

        if entries_dir.exists():
            shutil.rmtree(entries_dir)

        for year in range(self.get_start_year(), self.get_current_year() + 1):
            LinkDatabase.info("Writing bookmarks for a year {}".format(year))

            year_entries = self.get_entries(year)

            # do not differenciate export on language.
            # some entries could have not language at all, or some other foreign languages
            converter = EntryYearDataExporter(self.data_writer_config, year_entries)
            converter.export_entries(export_file_name = "bookmarks", export_path = entries_dir / str(year))

    def get_entries(self, year):
        start_date = datetime.date(year, 1, 1)
        stop_date = datetime.date(year + 1, 1, 1)

        therange = (start_date, stop_date)
        filters = self.get_configuration_filters()

        result_entries = []
        if self.user:
            bookmarks = UserBookmarks.get_user_bookmarks(self.user)
            # this returns IDs, not 'objects'
            result_entries = bookmarks.values_list("entry_object", flat=True)
            result_entries = LinkDataController.objects.filter(id__in=result_entries)
            result_entries = result_entries.filter(filters & Q(date_published__range=therange))
        else:
            result_entries = LinkDataController.objects.filter(
                filters & Q(date_published__range=therange)
            )

        return result_entries.order_by(*self.get_order_columns())

    def get_user(self):
        users = User.objects.filter(username=self.username)
        if users.count() > 0:
            return users[0]


class EntryYearTopicExporter(object):
    def __init__(self, MainExporter):
        super().__init__(data_writer_config)
        self._cfg = config

    def export(self, topic, directory):
        result_entries = self.get_entries()

        converter = EntryYearDataExporter(self.data_writer_config, result_entries)
        converter.export_entries(export_file_name = "topic_{}".format(topic), export_path=directory)

    def get_entries(self):
        tag_objs = UserTags.objects.filter(tag=topic)

        filters = self.get_configuration_filters()

        # this returns IDs, not 'objects'
        result_entries = tag_objs.values_list("entry_object", flat=True)
        result_entries = LinkDataController.objects.filter(filters & Q(id__in=result_entries))
        return result_entries.order_by(*self.get_order_columns())
