from django.db.models import Q

from utils.dateutils import DateUtils

from ..controllers import SourceDataController, LinkDataController
from ..controllers import LinkDataController
from .entriesexporter import EntriesExporter, MainExporter


class SourceEntriesDataExporter(object):
    def __init__(self, data_writer_config, source_url, filters):
        self.data_writer_config = data_writer_config
        self._cfg = data_writer_config.config

        self.source_url = source_url
        self.filters = filters

    def write_for_day(self, input_path, day_iso):
        entries = self.get_entries(day_iso)
        clean_url = self._cfg.get_url_clean_name(self.source_url)

        ex = EntriesExporter(self.data_writer_config, entries)
        ex.export_entries(source_url = self.source_url, export_file_name = clean_url, export_path = input_path)

    def get_entries(self, day_iso):
        date_range = DateUtils.get_range4day(day_iso)
        entries = LinkDataController.objects.filter(
            Q(source_url=self.source_url)
            & Q(date_published__range=date_range)
            & self.filters
        )
        return entries


class EntryDailyDataMainExporter(MainExporter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def write_for_day(self, input_path, day_iso):
        """We do not want to provide for each day cumulative view. Users may want to select which 'streams' are selected individually '"""

        # TODO we first obtain entries to obtain them later again - this could be cleaned up

        entries = self.get_entries(day_iso)
        self.write_source_entries(input_path, day_iso, entries)
        self.write_sourceless_entries(input_path, day_iso, entries)

    def write_source_entries(self, input_path, day_iso, entries):
        sources = set(entries.values_list("source", flat=True).distinct())

        for source_obj in sources:
            filters = super().get_configuration_filters()
            writer = SourceEntriesDataExporter(
                self.data_writer_config, source_obj.url, filters
            )
            writer.write_for_day(input_path, day_iso)

    def write_sourceless_entries(self, input_path, day_iso, entries):
        entries = entries.filter(Q(source_url__isnull = True) | Q(source_url = ""))

        e = EntriesExporter(self.data_writer_config, entries)
        e.export_entries(source_url = None, export_file_name="sourceless", export_path = input_path)

    def get_entries(self, day_iso):
        date_range = DateUtils.get_range4day(day_iso)

        # some entries might not have source in the database - added manually.
        # first capture entries, then check if has export to CMS.
        # if entry does not have source, it was added manually and is subject for export

        filters = super().get_configuration_filters()

        entries = LinkDataController.objects.filter(
            filters & Q(date_published__range=date_range)
        )

        return entries.order_by(*self.get_order_columns())
