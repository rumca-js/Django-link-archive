import traceback
from dateutil import parser

from .sourcegenericplugin import SourceGenericPlugin
from ..models import PersistentInfo, BaseLinkDataController


class BaseRssPlugin(SourceGenericPlugin):
    PLUGIN_NAME = "BaseRssPlugin"

    def __init__(self, source):
        super().__init__(source)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_link_props(self):
        try:
            import feedparser

            source = self.source

            url = source.url
            feed = feedparser.parse(url)
            return self.process_rss_feed(self.source, feed)

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.exc(
                "Source:{} {}; Exc:{}\n{}".format(
                    source.url, source.title, str(e), error_text
                )
            )

    def process_rss_feed(self, source, feed):
        props = []

        source = self.source
        num_entries = len(feed.entries)

        # print("Found rss source entry, feed size:{}".format(num_entries))

        if num_entries == 0:
            PersistentInfo.error(
                "Source:{0} {1}; Source has no data".format(source.url, source.title)
            )
        else:
            for feed_entry in feed.entries:
                entry_props = self.process_rss_entry(source, feed_entry)
                if entry_props is not None:
                    props.append(entry_props)

        # print("Number of new entries: {0}".format(len(props)))

        return props

    def process_rss_entry(self, source, feed_entry):
        try:
            from ..controllers import LinkDataController

            props = self.get_feed_entry_map(source, feed_entry)

            objs = LinkDataController.objects.filter(link=props["link"])

            if not objs.exists():
                if "title" not in props:
                    PersistentInfo.error(
                        "Source:{} {}; Entry:{} {} no title".format(
                            source.url, source.title, feed_entry.link, feed_entry.title
                        )
                    )
                    return None

                if not self.is_link_valid(props["link"]):
                    return None

                if "date_published" not in props:
                    PersistentInfo.error(
                        "Source:{} {}; Entry:{} {} missing published field".format(
                            source.url, source.title, feed_entry.link, feed_entry.title
                        )
                    )
                    return None

                return props

        except Exception as e:
            error_text = traceback.format_exc()
            PersistentInfo.error(
                "Source:{} {}; Entry:{} {}; Exc:{}\n{}".format(
                    source.url,
                    source.title,
                    feed_entry.link,
                    feed_entry.title,
                    str(e),
                    error_text,
                )
            )

            return False

    def get_feed_entry_map(self, source, feed_entry):
        from ..dateutils import DateUtils

        output_map = {}

        if hasattr(feed_entry, "description"):
            output_map["description"] = feed_entry.description[
                : BaseLinkDataController.get_description_length() - 2
            ]
        else:
            output_map["description"] = ""

        if hasattr(feed_entry, "media_thumbnail"):
            output_map["thumbnail"] = feed_entry.media_thumbnail[0]["url"]
        else:
            output_map["thumbnail"] = None

        if hasattr(feed_entry, "date_published"):
            try:
                dt = parser.parse(feed_entry.published)
                output_map["date_published"] = dt
            except Exception as e:
                PersistentInfo.error(
                    "Rss parser datetime invalid feed datetime:{}; Exc:{} {}\n{}".format(
                        feed_entry.published, str(e), ""
                    )
                )
                output_map["date_published"] = DateUtils.get_datetime_now_utc()

        elif self.allow_adding_with_current_time:
            output_map["date_published"] = DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            output_map["date_published"] = self.default_entry_timestamp
        else:
            output_map["date_published"] = DateUtils.get_datetime_now_utc()

        output_map["source"] = source.url
        output_map["title"] = feed_entry.title
        output_map["language"] = source.language
        output_map["link"] = feed_entry.link
        output_map["artist"] = source.title
        output_map["album"] = source.title

        if str(feed_entry.title).strip() == "" or feed_entry.title == "undefined":
            output_map["title"] = output_map["link"]

        if output_map["date_published"]:
            output_map["date_published"] = DateUtils.to_utc_date(
                output_map["date_published"]
            )

            if output_map["date_published"] > DateUtils.get_datetime_now_utc():
                output_map["date_published"] = DateUtils.get_datetime_now_utc()

        return output_map
