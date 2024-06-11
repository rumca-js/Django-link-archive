import logging
import shutil
from django.db.models import Q
from django.contrib.auth.models import User
import datetime

from ..models import AppLogging, UserBookmarks, UserTags
from ..apps import LinkDatabase
from ..controllers import LinkDataController
from .converters import (
    ModelCollectionConverter,
    JsonConverter,
    MarkDownDynamicConverter,
    RssConverter,
)


class BookmarksEntryExporter(object):
    def __init__(self, config, entries):
        self._entries = entries
        self._cfg = config

    def export(self, export_file_name="bookmarks", export_dir="default"):
        if self._entries.count() == 0:
            return

        if not export_dir.exists():
            export_dir.mkdir(parents=True, exist_ok=True)


        cc = ModelCollectionConverter(self._entries)
        items = cc.get_map_full()

        js_converter = JsonConverter(items)
        js_converter.set_export_columns(LinkDataController.get_all_export_names())

        file_name = export_dir / (export_file_name + "_entries.json")
        file_name.write_text(js_converter.export())

        column_order = ["title", "link", "date_published", "tags", "date_dead_since"]

        md = MarkDownDynamicConverter(items, column_order)
        md_text = md.export()

        file_name = export_dir / (export_file_name + "_entries.md")
        file_name.write_text(md_text)

        rss_conv = RssConverter(items)
        rss_text = rss_conv.export()

        file_name = export_dir / (export_file_name + "_entries.rss")
        file_name.write_text(self.use_rss_wrapper(rss_text))

    def get_entries(self):
        entries = LinkDataController.objects.filter(bookmarked=True)

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
            AppLogging.error(
                "Template exception {0} {1} {2} {3}".format(
                    template_text, str(map_data), str(e), error_text
                )
            )
        return ""


class BookmarksExporter(object):
    def __init__(self, config, username=""):
        self._cfg = config
        self.username = username

    def get_ordered_queryset(input_queryset):
        return input_queryset.order_by("date_published", "link")

    def get_start_year(self):
        """
        We export from oldest entries
        """
        entries = BookmarksExporter.get_ordered_queryset(
            LinkDataController.objects.all()
        )
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
        from ..dateutils import DateUtils

        today = DateUtils.get_date_today()
        year = int(DateUtils.get_datetime_year(today))
        return year

    def export(self, directory):
        entries_dir = directory

        if entries_dir.exists():
            shutil.rmtree(entries_dir)

        for year in range(self.get_start_year(), self.get_current_year() + 1):
            LinkDatabase.info("Writing bookmarks for a year {}".format(year))

            all_entries = self.get_entries(year)

            # do not differenciate export on language.
            # some entries could have not language at all, or some other foreign languages
            converter = BookmarksEntryExporter(self._cfg, all_entries)
            converter.export("bookmarks", entries_dir / str(year))

    def get_entries(self, year):
        start_date = datetime.date(year, 1, 1)
        stop_date = datetime.date(year + 1, 1, 1)

        therange = (start_date, stop_date)

        result_entries = []

        user = self.get_user()

        if user:
            bookmarks = UserBookmarks.get_user_bookmarks(user)
            # this returns IDs, not 'objects'
            result_entries = bookmarks.values_list("entry_object", flat=True)
            result_entries = LinkDataController.objects.filter(
                id__in=result_entries
            )
            result_entries = result_entries.filter(date_published__range=therange)
        else:
            result_entries = LinkDataController.objects.filter(
                bookmarked=True, date_published__range=therange
            )

        result_entries = BookmarksExporter.get_ordered_queryset(result_entries)

        return result_entries

    def get_user(self):
        users = User.objects.filter(username=self.username)
        if users.count() > 0:
            return users[0]


class BookmarksTopicExporter(object):
    def __init__(self, config):
        self._cfg = config

    def export(self, topic, directory):
        tag_objs = UserTags.objects.filter(tag=topic)

        # this returns IDs, not 'objects'
        result_entries = tag_objs.values_list("entry_object", flat=True)
        result_entries = LinkDataController.objects.filter(id__in=result_entries)
        result_entries = BookmarksExporter.get_ordered_queryset(result_entries)

        converter = BookmarksEntryExporter(self._cfg, result_entries)
        converter.export("topic_{}".format(topic), directory, "topics")
