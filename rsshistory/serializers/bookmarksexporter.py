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
       from ..models import RssSourceEntryDataModel
       entries = RssSourceEntryDataModel.objects.filter(persistent = True)

    def get_export_path(self):
       entries_dir = self._cfg.get_bookmarks_path()
       export_path = entries_dir

       if not export_path.exists():
           export_path.mkdir(parents = True, exist_ok = True)

       return export_path

    def export(self, export_file_name = 'bookmarks', export_dir = "default"):

       if len(self._entries) == 0:
           return

       export_path = self.get_export_path() / export_dir
       if not export_path.exists():
           export_path.mkdir(parents = True, exist_ok = True)

       from .converters import ModelCollectionConverter, JsonConverter, MarkDownConverter, RssConverter

       cc = ModelCollectionConverter(self._entries)
       items = cc.get_map_full()

       js_converter = JsonConverter(items)
       js_converter.set_export_columns(['source', 'title', 'description','link','date_published', 'persistent', 'dead', 'user', 'language', 'tags', 'comments'])

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

    def use_rss_wrapper(self, text, language = "en-US", link = "https://renegat0x0.ddns.net"):
        template = self.get_rss_template()

        map_data = {'channel_title' : "RSS archive", 'channel_description': "Link archive",
                    'channel_language' : language, 'channel_link' : link,
                    'channel_feed_url': link, 'channel_text' : text}
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
            PersistentInfo.error("Template exception {0} {1} {2} {3}".format(template_text, str(map_data), str(e), error_text))
        return ""


class BookmarksBigExporter(object):

    def __init__(self, config):
        self._cfg = config

    def get_start_year(self):
        return 1970

    def get_current_year(self):
        from ..dateutils import DateUtils
        today = DateUtils.get_date_today()
        year = int(DateUtils.get_datetime_year(today))
        return year

    def export(self):
       import datetime
       from ..models import RssSourceEntryDataModel

       entries_dir = self._cfg.get_bookmarks_path()
       if entries_dir.exists():
           shutil.rmtree(entries_dir)

       for year in range(self.get_start_year(), self.get_current_year() + 1):
           start_date = datetime.date(year,1,1)
           stop_date = datetime.date(year+1,1,1)

           therange = (start_date, stop_date)

           all_entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange)

           en_entries = all_entries.filter(language__icontains = 'en')
           pl_entries = all_entries.filter(language__icontains = 'pl')

           converter = BookmarksExporter(self._cfg, en_entries)
           converter.export('bookmarks_EN', str(year))

           converter = BookmarksExporter(self._cfg, pl_entries)
           converter.export('bookmarks_PL', str(year))

           #en_entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange, language__icontains = 'en')
           #converter = BookmarksExporter(self._cfg, en_entries)
           #converter.export('bookmarks_EN', str(year))

           #en_entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange, language__icontains = 'pl')
           #converter = BookmarksExporter(self._cfg, en_entries)
           #converter.export('bookmarks_PL', str(year))
