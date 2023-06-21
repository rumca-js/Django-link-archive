import logging

from .converters import ModelCollectionConverter, JsonConverter, MarkDownConverter


class EntriesExporter(object):
    def __init__(self, config, entries):
        self._entries = entries
        self._cfg = config

        self.md_template_link = ""
        self.md_template_link += "## $title\n"
        self.md_template_link += " - [$link]($link)\n"
        self.md_template_link += " - RSS feed: $source\n"
        self.md_template_link += " - date published: $date_published\n"
        self.md_template_link += "\n"
        self.md_template_link += "$description\n"

        self.source_template = "# Source:$title, URL:$url, language:$language"

    def export_entries(
        self,
        source_url,
        export_file_name="default",
        export_path=None,
        with_description=True,
    ):
        if len(self._entries) == 0:
            return

        if not export_path.exists():
            export_path.mkdir()

        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        js_converter = JsonConverter(items)
        js_converter.set_export_columns(
            [
                "source",
                "title",
                "description",
                "link",
                "date_published",
                "persistent",
                "dead",
                "user",
                "language",
                "tags",
                "comments",
            ]
        )

        file_name = export_path / (export_file_name + "_entries.json")
        file_name.write_text(js_converter.export())

        md = MarkDownConverter(items, self.md_template_link)
        md_text = md.export()

        from ..models import SourceDataModel

        sources = SourceDataModel.objects.filter(url=source_url)

        if sources.exists():
            from .converters import MarkDownSourceConverter

            msc = MarkDownSourceConverter(sources[0], self.source_template)
            msc_text = msc.export()
            md_text = msc_text + "\n\n" + md_text

        file_name = export_path / (export_file_name + "_entries.md")
        file_name.write_text(md_text)

    def export_all_entries(self, with_description=True):
        if len(self._entries) == 0:
            return

        entries_dir = self._cfg.get_export_path() / self._cfg.get_date_file_name()
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir()

        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        js_converter = JsonConverter(items)
        js_converter.set_export_columns(
            [
                "source",
                "title",
                "description",
                "link",
                "date_published",
                "persistent",
                "dead",
                "user",
                "language",
                "tags",
                "comments",
            ]
        )

        file_name = export_path / ("all_entries.json")
        file_name.write_text(js_converter.export())

        md = MarkDownConverter(items, self.md_template_link)
        md_text = md.export()

        file_name = export_path / ("all_entries.md")
        file_name.write_bytes(md_text.encode("utf-8", "ingnore"))
