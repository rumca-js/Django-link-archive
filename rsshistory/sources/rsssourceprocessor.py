import feedparser
import logging
import traceback

from ..models import PersistentInfo
from .basepluginbuilder import BasePluginBuilder


class RssSourceProcessor(object):

    def __init__(self, config):
        self._cfg = config
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def process_source(self, source):
        from ..dateutils import DateUtils

        try:
            print("process source: {0}".format(source.title))

            if not source.is_fetch_possible():
                print("Not time for source: {0}".format(source.title))
                return

            start_time = DateUtils.get_datetime_now_utc()

            num_entries = self.process_source_impl(source)

            stop_time = DateUtils.get_datetime_now_utc()
            total_time = stop_time - start_time
            total_time.total_seconds()

            if num_entries != 0:
                source.set_operational_info(stop_time, num_entries, total_time.total_seconds())

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))

    def process_source_impl(self, source):
        plugin = BasePluginBuilder.get(source.get_domain())
        num_entries = 0

        if plugin.is_rss_source():
            num_entries = self.process_rss_source(source)
        else:
            num_entries = self.process_parser_source(source)
        return num_entries

    def process_rss_source(self, source, url=None):
        try:
            import feedparser

            if url is None:
                url = source.url
            feed = feedparser.parse(url)
            # print("Feed parse: {}".format(str(feed)))

            num_entries = len(feed.entries)
            num_processed_entries = 0

            print("Found rss source entry")

            if num_entries == 0:
                PersistentInfo.error("Source:{0} {1}; Source has no data".format(source.url, source.title))
            else:
                # rss_path = self._cfg.get_export_path() / "downloaded_rss"
                # rss_path.mkdir(parents = True, exist_ok = True)

                # file_name = url + ".txt"
                # file_name = self._cfg.get_url_clean_name(file_name)

                # file_path = rss_path / file_name
                # file_path.write_text(str(feed))

                for entry in feed.entries:
                    if self.process_rss_entry(source, entry):
                        num_processed_entries += 1

            print("Number of processed entries: {0}".format(num_processed_entries))

            return num_processed_entries
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))

    def process_parser_source(self, source):
        from ..webtools import Page
        from ..models import RssSourceEntryDataModel
        try:
            plugin = BasePluginBuilder.get(source.get_domain())
            links = plugin.get_links()
            num_entries = len(links)

            for link in links:
                objs = RssSourceEntryDataModel.objects.filter(link=link)
                if objs.exists():
                    continue

                p = Page(link)
                title = p.get_title()
                if title:
                    props = plugin.get_link_data(source, link)

                    o = RssSourceEntryDataModel(
                        source=props['source'],
                        title=props['title'],
                        description=props['description'],
                        link=props['link'],
                        date_published=props['published'],
                        language=props['language'],
                        source_obj=source)

                    o.save()
                else:
                    print("Could not read title: {0}".format(link))
                    PersistentInfo.error("Could not read title: {0}".format(link))

            return num_entries
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))

    def process_rss_entry(self, source, feed_entry):
        try:
            from ..models import RssSourceEntryDataModel

            plugin = BasePluginBuilder.get(source.get_domain())
            plugin.allow_adding_with_current_time = self.allow_adding_with_current_time
            if self.default_entry_timestamp:
                plugin.default_entry_timestamp = self.default_entry_timestamp

            props = plugin.get_feed_entry_map(source, feed_entry)

            objs = RssSourceEntryDataModel.objects.filter(link=props['link'])

            if not objs.exists():
                if str(feed_entry.title).strip() == "" or feed_entry.title == "undefined":
                    return False

                if not plugin.is_link_valid(props['link']):
                    return False

                if 'published' not in props:
                    return False

                o = RssSourceEntryDataModel(
                    source=props['source'],
                    title=props['title'],
                    description=props['description'],
                    link=props['link'],
                    date_published=props['published'],
                    language=props['language'],
                    thumbnail=props['thumbnail'],
                    source_obj=source)
                try:
                    o.save()
                    return True
                except Exception as e:
                    print(str(e))
                    return False

            return True

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                    "Source:{} {}; Entry:{} {}; Exc:{}\n{}".format(source.url, source.title, feed_entry.link,
                                                              feed_entry.title, str(e), error_text))

            return False
