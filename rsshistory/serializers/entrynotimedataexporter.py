from pathlib import Path
from django.db.models import Q

from utils.serializers.converters import (
    ModelCollectionConverter,
    JsonConverter,
    MarkDownDynamicConverter,
    RssConverter,
    PageSystem,
)
from ..controllers import LinkDataController
from .entriesexporter import MainExporter, EntriesExporter


class EntryNoTimeDataExporter(EntriesExporter):
    def __init__(self, data_writer_config, entries):
        super().__init__(data_writer_config, entries)

    def items2mdtext(self, items):
        column_order = ["title", "link", "date_published", "tags", "date_dead_since"]
        md = MarkDownDynamicConverter(items, column_order)
        md_text = md.export()

        return md_text


class EntryNoTimeDataMainExporter(MainExporter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def export(self, export_file_name="permanents", export_path="default"):
        all_entries = self.get_entries()

        page_system = PageSystem(
            all_entries.count(), self.get_number_of_entries_for_page()
        )

        for page in range(page_system.no_pages):
            slice_limits = page_system.get_slice_limits(page)
            entries = all_entries[slice_limits[0] : slice_limits[1]]

            e = EntryNoTimeDataExporter(self.data_writer_config, entries)
            e.export_entries(export_file_name = "permanent", export_path = self.get_page_dir(export_path, page))

    def get_order_columns(self):
        return [ "domain_obj__tld",
                 "domain_obj__suffix",
                 "domain_obj__main",
                 "domain_obj__domain",
                 "date_published",
                 "link"]

    def get_page_dir(self, export_path, page):
        return export_path / Path("permanent") / "{page:05d}".format(page=page)

    def get_number_of_entries_for_page(self):
        return 1000
