import traceback
from dateutil import parser

from .baseplugin import BasePlugin
from ..models import PersistentInfo


class BaseRssPlugin(BasePlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source):
        super().__init__(source)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_link_props(self):
        try:
            import feedparser

            source = self.source
            props = []

            url = source.url
            feed = feedparser.parse(url)
            # print("Feed parse: {}".format(str(feed)))

            num_entries = len(feed.entries)
            num_processed_entries = 0

            print("Found rss source entry, feed size:{}".format(num_entries))

            if num_entries == 0:
                PersistentInfo.error("Source:{0} {1}; Source has no data".format(source.url, source.title))
            else:
                # rss_path = self._cfg.get_export_path() / "downloaded_rss"
                # rss_path.mkdir(parents = True, exist_ok = True)

                # file_name = url + ".txt"
                # file_name = self._cfg.get_url_clean_name(file_name)

                # file_path = rss_path / file_name
                # file_path.write_text(str(feed))

                for feed_entry in feed.entries:
                    entry_props = self.process_rss_entry(source, feed_entry)
                    if entry_props is not None:
                        props.append(entry_props)

            print("Number of new entries: {0}".format(len(props)))

            return props
        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc("Source:{} {}; Exc:{}\n{}".format(source.url, source.title, str(e), error_text))

    def process_rss_entry(self, source, feed_entry):
        try:
            from ..models import LinkDataModel

            props = self.get_feed_entry_map(source, feed_entry)

            objs = LinkDataModel.objects.filter(link=props['link'])

            if not objs.exists():
                if str(feed_entry.title).strip() == "" or feed_entry.title == "undefined":
                    PersistentInfo.error(
                        "Source:{} {}; Entry:{} {} no title".format(source.url, source.title, feed_entry.link,
                                                                    feed_entry.title))
                    return None

                if not self.is_link_valid(props['link']):
                    return None

                if 'published' not in props:
                    PersistentInfo.error(
                        "Source:{} {}; Entry:{} {} missing published field".format(source.url, source.title,
                                                                                   feed_entry.link,
                                                                                   feed_entry.title))
                    return None

                return props

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Source:{} {}; Entry:{} {}; Exc:{}\n{}".format(source.url, source.title, feed_entry.link,
                                                               feed_entry.title, str(e), error_text))

            return False

    def get_feed_entry_map(self, source, feed_entry):
        from ..dateutils import DateUtils
        output_map = {}

        # print("feed entry dict: {}".format(feed_entry.__dict__))
        # print("Feed entry: {}".format(str(feed_entry)))

        if hasattr(feed_entry, "description"):
            output_map['description'] = feed_entry.description
        else:
            output_map['description'] = ""

        if hasattr(feed_entry, "media_thumbnail"):
            output_map['thumbnail'] = feed_entry.media_thumbnail[0]['url']
        else:
            output_map['thumbnail'] = None

        if hasattr(feed_entry, "published"):
            try:
                dt = parser.parse(feed_entry.published)
                output_map['published'] = dt
            except Exception as e:
                PersistentInfo.error(
                    "Rss parser datetime invalid feed datetime:{}; Exc:{} {}\n{}".format(feed_entry.published,
                                                                                         str(e), error_text))
                output_map['published'] = DateUtils.get_datetime_now_utc()

        elif self.allow_adding_with_current_time:
            output_map['published'] = DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            output_map['published'] = self.default_entry_timestamp
        else:
            output_map['published'] = DateUtils.get_datetime_now_utc()

        output_map['source'] = source.url
        output_map['title'] = feed_entry.title
        output_map['language'] = source.language
        output_map['link'] = feed_entry.link

        if output_map['published']:
            output_map['published'] = DateUtils.to_utc_date(output_map['published'])

            if output_map['published'] > DateUtils.get_datetime_now_utc():
                output_map['published'] = DateUtils.get_datetime_now_utc()

        return output_map