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

       """
       e_converter = EntriesConverter()
       e_converter.set_entries(self._entries)
       e_converter.with_description = False
       e_converter.with_tags = True

       file_name = export_path / (export_file_name + "_entries.json")
       #log.info("writing json: " + file_name.as_posix() )
       file_name.write_text(e_converter.get_json())

       file_name = export_path / (export_file_name + "_entries.md")
       #log.info("writing md: " + file_name.as_posix() )
       file_name.write_bytes(e_converter.get_md_text().encode("utf-8", "ingnore"))

       file_name = export_path / (export_file_name + "_entries.rss")
       #log.info("writing rss: " + file_name.as_posix() )
       text = e_converter.get_rss_text()
       text = self.encapsulate_rss(text)
       file_name.write_bytes(text.encode("utf-8", "ingnore"))
       """

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
       file_name.write_text(rss_text)

    def get_rss_template(self, text, language = "en-US"):
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
  <title>RSS history</title>
  <atom:link href="https://renegat0x0.ddns.net/feed" rel="self" type="application/rss+xml" />
  <link>https://renegat0x0.ddns.net/</link>
  <description>RSS archive</description>
  <language>$language</language>
$text
</channel></rss>
"""
       return text


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

           # entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange)
           # converter = BookmarksExporter(self._cfg, entries)
           # converter.export('bookmarks_ALL', str(year))

           en_entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange, language__icontains = 'en')
           converter = BookmarksExporter(self._cfg, en_entries)
           converter.export('bookmarks_EN', str(year))

           en_entries = RssSourceEntryDataModel.objects.filter(persistent = True, date_published__range=therange, language__icontains = 'pl')
           converter = BookmarksExporter(self._cfg, en_entries)
           converter.export('bookmarks_PL', str(year))
