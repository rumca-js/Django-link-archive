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

    def items2mdtext(self, items, source_url=None):
        column_order = ["title", "link", "date_published", "tags", "date_dead_since"]
        md = MarkDownDynamicConverter(items, column_order)
        md_text = md.export()

        return md_text


class EntryNoTimeDataMainExporter(MainExporter):
    def __init__(self, data_writer_config):
        super().__init__(data_writer_config)

    def export(self, export_file_name="permanents", export_path="default"):
        # we could try using in bulk
        number_of_all_entries = self.get_entries().count()

        page_system = PageSystem(
            number_of_all_entries, self.get_number_of_entries_for_page()
        )

        for page in range(page_system.no_pages):
            # we cannot reuse all_entries, as more and more data are fetched from it
            # https://stackoverflow.com/questions/44206636/how-to-bulk-fetch-model-objects-from-database-handled-by-django-sqlalchemy

            search_entries = self.get_entries()
            slice_limits = page_system.get_slice_limits(page)
            entries = search_entries[slice_limits[0] : slice_limits[1]]

            e = EntryNoTimeDataExporter(self.data_writer_config, entries)
            e.export_entries(
                export_file_name="permanent",
                export_path=self.get_page_dir(export_path, number_of_all_entries, page),
            )

    def get_order_columns(self):
        return [
            "domain__tld",
            "domain__suffix",
            "domain__main",
            "domain__domain",
            "date_published",
            "link",
        ]

    def get_page_dir(self, export_path, number_of_all_entries, page):
        number_of_all_entries_str = str(number_of_all_entries)
        char_len = len(number_of_all_entries_str)

        if char_len > 5:
            page_dir = str(page).zfill(char_len)
        else:
            page_dir = "{page:05d}".format(page=page)

        return export_path / Path("permanent") / page_dir

    def get_number_of_entries_for_page(self):
        return 1000
