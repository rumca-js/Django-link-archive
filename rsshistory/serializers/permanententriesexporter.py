from ..controllers import LinkDataController
from pathlib import Path

from .converters import (
    ModelCollectionConverter,
    JsonConverter,
    MarkDownConverter,
    RssConverter,
    PageSystem,
)


class PermanentEntriesExporter(object):
    def __init__(self, config):
        self._cfg = config

        self.md_template_bookmarked = ""
        self.md_template_bookmarked += "## $title\n"
        self.md_template_bookmarked += " - [$link]($link)\n"
        self.md_template_bookmarked += " - date published: $date_published\n"
        self.md_template_bookmarked += " - user: $user\n"
        self.md_template_bookmarked += " - tags: $tags\n"

    def export(self, export_file_name="permanents", export_path="default"):
        # TODO rewrite this to use batch jobs. You cannot iterate over whole database
        all_entries = LinkDataController.objects.filter(permanent=True).order_by(
            "domain_obj__tld",
            "domain_obj__suffix",
            "domain_obj__main",
            "domain_obj__domain",
            "date_published",
            "link",
        )

        page_system = PageSystem(
            all_entries.count(), self.get_number_of_entries_for_page()
        )

        for page in range(page_system.no_pages):
            slice_limits = page_system.get_slice_limits(page)
            entries = all_entries[slice_limits[0] : slice_limits[1]]

            self.export_inner(
                entries, "permanent", self.get_page_dir(export_path, page)
            )

    def get_page_dir(self, export_path, page):
        return export_path / Path("permanent") / "{page:05d}".format(page=page)

    def export_inner(
        self, entries, export_file_name="permanent", export_path="default"
    ):
        if entries.count() == 0:
            return

        export_path.mkdir(parents=True, exist_ok=True)

        from ..controllers import LinkDataController

        cc = ModelCollectionConverter(entries)
        items = cc.get_map_full()

        js_converter = JsonConverter(items)
        js_converter.set_export_columns(LinkDataController.get_all_export_names())

        file_name = export_path / (export_file_name + "_entries.json")
        file_name.write_text(js_converter.export())

        md = MarkDownConverter(items, self.md_template_bookmarked)
        md_text = md.export()

        file_name = export_path / (export_file_name + "_entries.md")
        file_name.write_text(md_text)

    def get_number_of_entries_for_page(self):
        return 1000
