
from ..webtools import Page

class BasePlugin(Page):
    def __init__(self):
        super().__init__(self.get_address())
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_address(self):
        return "https://google.com"

    def get_processing_type(self):
        return "RSS"

    def is_rss_source(self):
        if self.get_processing_type() == "RSS":
            return True
        return False

    def is_link_valid(self, address):
        return True

    def get_link_data(self, source, link):
        from ..dateutils import DateUtils
        output_map = {}

        link_ob = Page(link)

        title = link_ob.get_title()

        output_map['link'] = link
        output_map['title'] = title
        output_map['description'] = title
        output_map['source'] = source.url
        output_map['published'] = DateUtils.get_datetime_now_utc()
        output_map['language'] = source.language
        return output_map

    def get_feed_entry_map(self, source, feed_entry):
        from ..dateutils import DateUtils
        output_map = {}

        #print("feed entry dict: {}".format(feed_entry.__dict__))
        #print("Feed entry: {}".format(str(feed_entry)))

        if hasattr(feed_entry, "description"):
            output_map['description'] = feed_entry.description
        else:
            output_map['description'] = ""

        if hasattr(feed_entry, "media_thumbnail"):
            output_map['thumbnail'] = feed_entry.media_thumbnail[0]['url']
        else:
            output_map['thumbnail'] = None

        if hasattr(feed_entry, "published"):
            output_map['published'] = DateUtils.get_iso_datetime(feed_entry.published)
        elif self.allow_adding_with_current_time:
            output_map['published'] = DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            output_map['published'] = self.default_entry_timestamp
        else:
            output_map['published'] = ""

        output_map['source'] = source.url
        output_map['title'] = feed_entry.title
        output_map['language'] = source.language
        output_map['link'] = feed_entry.link

        return output_map
