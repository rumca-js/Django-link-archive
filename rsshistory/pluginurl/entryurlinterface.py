from ..webtools import HtmlPage, RssPage, BasePage, Url, PageOptions
from ..dateutils import DateUtils
from ..controllers import SourceDataController

from ..apps import LinkDatabase
from ..models import PersistentInfo

from .urlhandler import UrlHandler


class YouTubeException(Exception):
    pass


class EntryUrlInterface(object):
    """
    Provides interface between Entry and URL properties.
    """

    def __init__(
        self, url, fast_check=True, use_selenium=False, log=False, ignore_errors=False
    ):
        """
        Some scenarios, like manual entry should log why it is impossible to check
        TODO maybe add ignore_errors, so we could add any kind of link?
        """
        self.url = url
        self.log = log
        self.ignore_errors = ignore_errors

        if self.url.endswith("/"):
            self.url = self.url[:-1]

        self.p = UrlHandler.get(
            self.url, fast_check=fast_check, use_selenium=use_selenium
        )

    def get_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        props = self.get_props_implementation(input_props)

        # we do not trim description here. We might need it later, when adding link we scan
        # description for URLs

        if props:
            is_domain = BasePage(self.url).is_domain()
            if is_domain and ("thumbnail" not in props or props["thumbnail"] == None):
                if "favicons" in props:
                    favicons = props["favicons"]
                    if favicons and len(favicons) > 0:
                        props["thumbnail"] = favicons[0][0]

            props["page_rating_contents"] = self.p.get_page_rating()
            props["page_rating"] = self.p.get_page_rating()

            if not self.is_property_set(props, "artist") and self.p.get_author():
                props["artist"] = self.p.get_author()

        return props

    def get_props_implementation(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        if not self.is_property_set(input_props, "source"):
            if source_obj:
                input_props["source"] = source_obj.url

        is_domain = BasePage(self.url).is_domain()
        p = self.p

        if is_domain:
            input_props["permanent"] = True
            input_props["bookmarked"] = False

        if not source_obj:
            sources = SourceDataController.objects.filter(url=self.url)
            if sources.exists():
                source_obj = sources[0]

        if not self.is_property_set(input_props, "source_obj") and source_obj:
            input_props["source_obj"] = source_obj

        if not self.is_property_set(input_props, "source") and source_obj:
            input_props["source"] = source_obj.url

        if type(p) is UrlHandler.youtube_video_handler:
            if p.get_video_code():
                return self.get_youtube_props(input_props)

        if p.is_html():
            return self.get_htmlpage_props(input_props, source_obj)

        if p.is_rss():
            return self.get_rsspage_props(input_props, source_obj)

        # TODO provide RSS support

    def get_youtube_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        p = self.p

        if not self.ignore_errors and not p.is_valid():
            if self.log:
                LinkDatabase.info("YouTube page is invalid:{}".format(url))
                PersistentInfo.error("YouTube page is invalid:{}".format(url))
            return None

        source_url = p.get_channel_feed_url()
        if source_url is None:
            PersistentInfo.error(
                "Could not obtain channel feed url:{}".format(source_url)
            )

        # always use classic link format in storage
        input_props["link"] = p.get_link_classic()

        if not self.is_property_set(input_props, "title"):
            input_props["title"] = p.get_title()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = p.get_description()
        if not self.is_property_set(input_props, "date_published"):
            input_props["date_published"] = p.get_datetime_published()
        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()

        # https://help.indiefy.net/hc/en-us/articles/360047860834-What-is-a-YouTube-topic-channel-and-how-does-it-work-
        channel_name = p.get_channel_name()
        if channel_name:
            wh_channel = channel_name.find("- Topic")
            if wh_channel >= 0:
                channel_name = channel_name[:wh]

        if not self.is_property_set(input_props, "artist"):
            input_props["artist"] = channel_name
        if not self.is_property_set(input_props, "album"):
            input_props["album"] = channel_name

        if not self.is_property_set(input_props, "language") and source_obj:
            input_props["language"] = source_obj.language

        if source_url:
            input_props["source"] = source_url

        input_props["live"] = p.is_live()

        return input_props

    def get_htmlpage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        p = self.p

        if not self.ignore_errors and not p.is_valid():
            if self.log:
                LinkDatabase.info("HTML page is invalid:{}".format(url))
                PersistentInfo.error("HTML page is invalid:{}".format(url))
            return None

        # some pages return invalid code / information. let the user decide
        # what to do about it

        if not self.is_property_set(input_props, "link"):
            input_props["link"] = p.url
        if not self.is_property_set(input_props, "title"):
            title = p.get_title()
            input_props["title"] = title
        if not self.is_property_set(input_props, "description"):
            description = p.get_description()
            if description is None:
                if self.is_property_set(input_props, "title"):
                    description = input_props["title"]
            input_props["description"] = description

        if not self.is_property_set(input_props, "language"):
            language = p.get_language()
            if not language:
                if source_obj:
                    language = source_obj.language
            input_props["language"] = language

        if not self.is_property_set(input_props, "date_published"):
            date = p.get_date_published()
            if date:
                input_props["date_published"] = date
            else:
                date = p.guess_date()
                if date:
                    input_props["date_published"] = date
                else:
                    input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()

        input_props["page_rating_contents"] = p.get_page_rating()

        return input_props

    def get_rsspage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        if url.startswith("http://"):
            url = url.replace("http://", "https://")

        p = self.p

        if not self.ignore_errors and not p.is_valid():
            if self.log:
                LinkDatabase.info("RSS page is invalid:{}".format(url))
                PersistentInfo.error("HTML page is invalid:{}".format(url))
            return None

        if not self.is_property_set(input_props, "link"):
            input_props["link"] = p.url
        if not self.is_property_set(input_props, "title"):
            title = p.get_title()
            input_props["title"] = title
        if not self.is_property_set(input_props, "description"):
            description = p.get_description()
            if description is None:
                description = title
            input_props["description"] = description

        if not self.is_property_set(input_props, "language"):
            language = p.get_language()
            if not language:
                if source_obj:
                    language = source_obj.language
            input_props["language"] = language

        if not self.is_property_set(input_props, "date_published"):
            date = p.get_date_published()
            if date:
                input_props["date_published"] = date
            else:
                input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()

        input_props["page_rating_contents"] = p.get_page_rating()

        return input_props

    def update_info_default(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url
        p = self.p

        if not p.is_valid():
            LinkDatabase.info("HTML page is invalid:{}".format(url))
            return

        if not self.is_property_set(input_props, "source"):
            input_props["source"] = self.url
        if not self.is_property_set(input_props, "language"):
            input_props["language"] = None
        if not self.is_property_set(input_props, "title"):
            input_props["title"] = p.get_domain()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = p.get_domain()

        input_props["page_rating_contents"] = p.get_page_rating()

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
