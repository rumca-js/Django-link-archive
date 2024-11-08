import logging
from string import Template

from django.db.models import Q

from utils.serializers.converters import (
    ModelCollectionConverter,
    JsonConverter,
    MarkDownConverter,
    MarkDownSourceConverter,
    RssConverter,
    MarkDownDynamicConverter,
)
from utils.serializers import (
    HtmlExporter,
)
from ..controllers import SourceDataController, LinkDataController


class EntriesExporter(object):
    """
    Food for thought:
     - maybe we should accept ModelCollection, rather than db objects?
     - we would not be dependent on DB, and we could move to utils
     - we could iterate entry over entry, and override how entry should be added
     - if file was handle we could write as to a file
     - if format is ZIP, we would just print normally, then zip everything
     - if format is HTML, we would print differently
     - if format is SQLite, we would insert there only
    """

    def __init__(self, data_writer_config, entries):
        self._entries = entries
        self.data_writer_config = data_writer_config
        self._cfg = data_writer_config.config

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
        source_url=None,
        export_file_name="default",
        export_path=None,
        with_description=True,
    ):
        if self._entries.count() == 0:
            return

        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)

        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        export_config = self.data_writer_config.export_config

        self.add_all(items, export_path, export_file_name, source_url)

    def add_all(self, items, export_path, export_file_name, source_url=None):

        export_config = self.data_writer_config.export_config
        if export_config.format_json:
            json_text = self.items2jsontext(items)
            file_name = export_path / (export_file_name + "_entries.json")
            file_name.write_text(json_text)

        if export_config.format_md:
            md_text = self.items2mdtext(items=items, source_url=source_url)
            file_name = export_path / (export_file_name + "_entries.md")
            file_name.write_text(md_text)

        if export_config.format_rss:
            rss_text = self.items2rsstext(items)

            file_name = export_path / (export_file_name + "_entries.rss")
            file_name.write_text(rss_text)

        if export_config.format_html:
            p = export_path / "html"
            if not p.exists():
                p.mkdir(parents=True, exist_ok=True)
            e = HtmlExporter(p, self._entries)
            e.write()

        if export_config.output_sqlite:
            self.items2sqlite(items, export_path, export_file_name)

    def items2jsontext(self, items):
        js_converter = JsonConverter(items)
        js_converter.set_export_columns(LinkDataController.get_all_export_names())
        return js_converter.export()

    def items2mdtext(self, items, source_url=None):
        md = MarkDownConverter(items, self.md_template_link)
        md_text = md.export()

        if source_url:
            sources = SourceDataController.objects.filter(url=source_url)
            if sources.exists():
                msc = MarkDownSourceConverter(sources[0], self.source_template)
                msc_text = msc.export()
                md_text = msc_text + "\n\n" + md_text

        return md_text

    def items2rsstext(self, items):
        rss_conv = RssConverter(items)
        rss_text = rss_conv.export()

        return self.use_rss_wrapper(rss_text, rss_file_name=str(file_name))

    def items2sqlite(self, items, export_path, export_file_name):
        from utils.sqlmodel import SqlModel
        from utils.controllers import EntryDataBuilder

        connection = SqlModel(export_path / export_file_name)
        builder = EntryDataBuilder(connection)
        for item in items:
            builder.build(link_data=item)

    def export_all_entries(self, with_description=True):
        if self._entries.count() == 0:
            return

        entries_dir = self._cfg.get_export_path() / self._cfg.get_date_file_name()
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir()

        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        export_config = self.data_writer_config.export_config
        if export_config.format_json:
            self.items2jsontext(items)

            file_name = export_path / ("all_entries.json")
            file_name.write_text(js_converter.export())

        if export_config.format_md:
            self.items2mdtext(items)

            file_name = export_path / ("all_entries.md")
            file_name.write_bytes(md_text.encode("utf-8", "ingnore"))

        if export_config.format_rss:
            rss_text = self.items2rsstext(items)

            file_name = export_path / ("all_entries.rss")
            file_name.write_text(rss_text)

    def use_rss_wrapper(self, text, language="en", rss_file_name=None):
        template = self.get_rss_template()

        link = self._cfg.instance_internet_location
        title = self._cfg.instance_title
        description = self._cfg.instance_description

        if not rss_file_name:
            rss_file_name = link

        map_data = {
            "channel_title": title,
            "channel_description": description,
            "channel_language": language,
            "channel_link": link,
            "channel_feed_url": rss_file_name,
            "channel_text": text,
        }
        return self.use_template(template, map_data)

    def get_rss_template(self):
        text = """
<?xml version="1.0" encoding="UTF-8" ?><rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/"
	xmlns:wfw="http://wellformedweb.org/CommentAPI/"
	xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:atom="http://www.w3.org/2005/Atom"
	xmlns:sy="http://purl.org/rss/1.0/modules/syndication/"
	xmlns:slash="http://purl.org/rss/1.0/modules/slash/"
        xmlns:webfeeds="http://webfeeds.org/rss/1.0"
	
xmlns:georss="http://www.georss.org/georss" xmlns:geo="http://www.w3.org/2003/01/geo/wgs84_pos#">
<channel>
  <title>$channel_title</title>
  <atom:link href="$channel_feed_url" rel="self" type="application/rss+xml" />
  <link>$channel_link/</link>
  <description>$channel_description</description>
  <language>$channel_language</language>
$channel_text
</channel></rss>
"""
        return text

    def use_template(self, template_text, map_data):
        try:
            t = Template(template_text)
            return t.safe_substitute(map_data)
        except KeyError as E:
            AppLogging.exc(
                E,
                "Template exception {0} {1}".format(
                    template_text,
                    str(map_data),
                ),
            )
        return ""


class MainExporter(object):
    def __init__(self, data_writer_config, user=None):
        """
        @user if specified, then entries need to be written down according to 'user'
        """
        self._cfg = data_writer_config.config
        self.data_writer_config = data_writer_config
        self.user = user

    def get_configuration_filters(self):
        export_config = self.data_writer_config.export_config

        filters = Q()

        if not export_config.export_entries:
            return filters

        if export_config.export_entries_bookmarks:
            if filters == Q():
                filters = Q(bookmarked=True)
            else:
                filters |= Q(bookmarked=True)

        if export_config.export_entries_permanents:
            if filters == Q():
                filters = Q(permanent=True)
            else:
                filters = filters | Q(permanent=True)

        return filters

    def get_order_columns(self):
        return "date_published", "link"

    def get_entries(self):
        export_config = self.data_writer_config.export_config
        if not export_config.export_entries:
            return LinkDataController.objects.none()

        filters = self.get_configuration_filters()
        entries = LinkDataController.objects.filter(filters)
        return entries.order_by(*self.get_order_columns())
