from ..webtools import HtmlPage, RssPage, DomainAwarePage, Url, PageOptions
from ..dateutils import DateUtils
from ..controllers import SourceDataController, LinkDataController

from ..apps import LinkDatabase
from ..models import AppLogging

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
        self.log = log
        self.ignore_errors = ignore_errors

        self.url = UrlHandler.get_cleaned_link(url)

        options = UrlHandler.get_url_options(url)
        options.fast_parsing = fast_check
        options.use_selenium_headless = use_selenium

        self.h = UrlHandler(self.url, page_options=options)
        if self.h.response:
            self.url = self.h.response.url

        if not self.ignore_errors and not self.h.is_valid():
            if self.log:
                LinkDatabase.info("Page is invalid:{}".format(url))
                AppLogging.error("Page is invalid:{}".format(url))
            self.p = None
            return None

        else:
            self.p = self.h.p

    def get_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        ignore_errors = self.ignore_errors
        props = self.get_props_implementation(input_props, source_obj)

        # we do not trim description here. We might need it later, when adding link we scan
        # description for URLs

        if props:
            self.update_info_default(props, source_obj)

        elif ignore_errors:
            props = {}
            props["link"] = self.url
            props["title"] = None
            props["description"] = None
            props["author"] = None
            props["language"] = None
            props["thumbnail"] = None
            props["date_published"] = DateUtils.get_datetime_now_utc()
            props["date_dead_since"] = DateUtils.get_datetime_now_utc()
            props["page_rating"] = 0
            props["page_rating_contents"] = 0
            props["status_code"] = LinkDataController.STATUS_DEAD

        return props

    def get_props_implementation(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        if not self.p:
            return None

        if not self.is_property_set(input_props, "source"):
            if source_obj:
                input_props["source"] = source_obj.url

        is_domain = DomainAwarePage(self.url).is_domain()
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
                return self.get_youtube_props(input_props, source_obj)

        if type(p) is HtmlPage:
            return self.get_htmlpage_props(input_props, source_obj)

        if type(p) is RssPage or type(p) is UrlHandler.youtube_channel_handler:
            return self.get_rsspage_props(input_props, source_obj)

        # TODO provide RSS support

    def get_youtube_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        p = self.p

        source_url = p.get_channel_feed_url()
        if source_url is None:
            AppLogging.error("Could not obtain channel feed url:{}".format(source_url))

        # always use classic link format in storage
        input_props["link"] = p.get_link_classic()

        if not self.is_property_set(input_props, "title"):
            input_props["title"] = p.get_title()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = p.get_description()
        if not self.is_property_set(input_props, "date_published"):
            input_props["date_published"] = p.get_date_published()
        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()

        # https://help.indiefy.net/hc/en-us/articles/360047860834-What-is-a-YouTube-topic-channel-and-how-does-it-work-
        channel_name = p.get_author()
        if channel_name:
            wh_channel = channel_name.find("- Topic")
            if wh_channel >= 0:
                channel_name = channel_name[:wh_channel]

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

        return input_props

    def get_rsspage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        p = self.p

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

        return input_props

    def update_info_default(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url
        h = self.h
        p = self.p

        if not self.is_property_set(input_props, "link"):
            input_props["link"] = self.url
        if not self.is_property_set(input_props, "title"):
            input_props["title"] = p.get_title()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = p.get_description()
        if not self.is_property_set(input_props, "language"):
            input_props["language"] = p.get_language()
        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()
        if not self.is_property_set(input_props, "author"):
            input_props["author"] = p.get_thumbnail()
        if not self.is_property_set(input_props, "album"):
            input_props["album"] = p.get_thumbnail()
        if not self.is_property_set(input_props, "page_rating_contents"):
            input_props["page_rating_contents"] = self.h.get_page_rating()
        if not self.is_property_set(input_props, "page_rating"):
            input_props["page_rating"] = self.h.get_page_rating()
        if not self.is_property_set(input_props, "status_code"):
            input_props["status_code"] = self.h.get_status_code()

        """
        Sometimes we want thumbnail sometimes we want favicon.
         - for search engine we want to store path to favicon if thumbnail is not available
         - for domains we want to store path to favicon if thumbnail is not available
         - for not domains? this is not clear cut. If entry is obtained by source, then source thumbnail should be displayed
        """

        is_domain = DomainAwarePage(self.url).is_domain()
        if is_domain and not self.is_property_set(input_props, "thumbnail"):
            if type(p) is HtmlPage and self.h:
                input_props["thumbnail"] = self.h.get_favicon()

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]
