import logging
import shutil
from ..models import PersistentInfo


class BookmarksExporter(object):
    def __init__(self, config, entries):
        self._entries = entries
        self._cfg = config

        self.md_template_bookmarked = ""
        self.md_template_bookmarked += "## $title\n"
        self.md_template_bookmarked += " - [$link]($link)\n"
        self.md_template_bookmarked += " - date published: $date_published\n"
        self.md_template_bookmarked += " - user: $user\n"
        self.md_template_bookmarked += " - tags: $tags\n"

    def get_entries(self):
        from ..controllers import LinkDataController

        entries = LinkDataController.objects.filter(bookmarked=True)

    def get_export_path(self):
        entries_dir = self._cfg.get_bookmarks_path()
        export_path = entries_dir

        if not export_path.exists():
            export_path.mkdir(parents=True, exist_ok=True)

        return export_path

    def export(self, export_file_name="bookmarks", export_dir="default"):
        if self._entries.count() == 0:
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

        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        js_converter = JsonConverter(items)
        js_converter.set_export_columns(LinkDataController.get_all_export_names())

        file_name = export_path / (export_file_name + "_entries.json")
        file_name.write_text(js_converter.export())

        md = MarkDownConverter(items, self.md_template_bookmarked)
        md_text = md.export()

        file_name = export_path / (export_file_name + "_entries.md")
        file_name.write_text(md_text)

        rss_conv = RssConverter(items)
        rss_text = rss_conv.export()

        file_name = export_path / (export_file_name + "_entries.rss")
        file_name.write_text(self.use_rss_wrapper(rss_text))

    # TODO remove hardcoded link to this site
    def use_rss_wrapper(self, text, language="en", link="https://renegat0x0.ddns.net"):
        template = self.get_rss_template()

        map_data = {
            "channel_title": "RSS archive",
            "channel_description": "Link archive",
            "channel_language": language,
            "channel_link": link,
            "channel_feed_url": link,
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
        from string import Template

        try:
            t = Template(template_text)
            return t.safe_substitute(map_data)
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Template exception {0} {1} {2} {3}".format(
                    template_text, str(map_data), str(e), error_text
                )
            )
        return ""


class BookmarksBigExporter(object):
    def __init__(self, config):
        self._cfg = config

    def get_start_year(self):
        return 1900

    def get_current_year(self):
        from ..dateutils import DateUtils

        today = DateUtils.get_date_today()
        year = int(DateUtils.get_datetime_year(today))
        return year

    def export(self):
        import datetime
        from ..controllers import LinkDataController

        entries_dir = self._cfg.get_bookmarks_path()
        if entries_dir.exists():
            shutil.rmtree(entries_dir)

        for year in range(self.get_start_year(), self.get_current_year() + 1):
            print("Writing bookmarks for a year {}".format(year))

            start_date = datetime.date(year, 1, 1)
            stop_date = datetime.date(year + 1, 1, 1)

            therange = (start_date, stop_date)

            all_entries = LinkDataController.objects.filter(
                bookmarked=True, date_published__range=therange
            )

            en_entries = all_entries.filter(language__icontains="en")
            pl_entries = all_entries.filter(language__icontains="pl")

            converter = BookmarksExporter(self._cfg, en_entries)
            converter.export("bookmarks_EN", str(year))

            converter = BookmarksExporter(self._cfg, pl_entries)
            converter.export("bookmarks_PL", str(year))


class BookmarksTopicExporter(object):
    def __init__(self, config):
        self._cfg = config

    def export(self, topic):
        import datetime
        from ..models import RssEntryTagsDataModel
        from ..controllers import LinkDataController

        tag_objs = RssEntryTagsDataModel.objects.filter(tag=topic)
        entries = set()
        for tag_obj in tag_objs:
            if tag_obj.link_obj is not None:
                entries.add(tag_obj.link_obj)

        entries = list(entries)
        entries = sorted(entries, key=lambda x: x.date_published)

        converter = BookmarksExporter(self._cfg, entries)
        converter.export("topic_{}".format(topic), "topics")
