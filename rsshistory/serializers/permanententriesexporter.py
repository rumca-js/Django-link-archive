from ..controllers import LinkDataController
from pathlib import Path


class PermanentEntriesExporter(object):
    def __init__(self, config):
        self._cfg = config

        self.md_template_bookmarked = ""
        self.md_template_bookmarked += "## $title\n"
        self.md_template_bookmarked += " - [$link]($link)\n"
        self.md_template_bookmarked += " - date published: $date_published\n"
        self.md_template_bookmarked += " - user: $user\n"
        self.md_template_bookmarked += " - tags: $tags\n"

    def export(self, export_file_name="permanents", export_dir="default"):
        # TODO rewrite this to use batch jobs. You cannot iterate over whole database
        all_entries = LinkDataController.objects.filter(
            permanent=True
        ).order_by("domain_obj__tld", "domain_obj__suffix", "domain_obj__main", "domain_obj__domain")

        entries_no = self.get_number_of_entries_for_page()
        pages_float = all_entries.count() / entries_no
        pages = int(pages_float)
        if pages_float > pages:
            pages += 1
        
        for page in range(pages):
            start_slice = page * entries_no
            end_slice = ((page+1) * entries_no)-1
            entries = all_entries[start_slice: end_slice]
            self.export_inner(entries, "permanent", self.get_page_dir(page))

    def get_page_dir(self, page):
        return Path("permement") / "{page:05d}".format(page=page)

    def export_inner(self, entries, export_file_name="permanent", export_dir="default"):
        if entries.count() == 0:
            return

        export_path = self.get_export_path() / export_dir
        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)

        from ..controllers import LinkDataController
        from .converters import (
            ModelCollectionConverter,
            JsonConverter,
            MarkDownConverter,
            RssConverter,
        )

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

    def get_export_path(self):
        entries_dir = self._cfg.get_bookmarks_path()
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)
        return export_path

    def get_number_of_entries_for_page(self):
        return 1000
