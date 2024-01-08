from ..webtools import HtmlPage, RssPage, BasePage, Url
from ..dateutils import DateUtils
from ..controllers import SourceDataController

from ..apps import LinkDatabase
from ..models import PersistentInfo

from .handlervideoyoutube import YouTubeVideoHandler
from .handlervideoodysee import OdyseeVideoHandler

from .handlerchannelyoutube import YouTubeChannelHandler
from .handlerchannelodysee import OdyseeChannelHandler


class YouTubeException(Exception):
    pass


class EntryUrlInterface(object):
    """
    Provides interface between Entry and URL properties.
    """

    def __init__(self, url):
        self.url = url

        if self.url.endswith("/"):
            self.url = self.url[:-1]

        self.p = UrlHandler.get(self.url)

    def get_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        props = self.get_props_implementation(input_props)

        if props:
            if self.is_property_set(input_props, "description"):
                if len(props["description"]) > 950:
                    # TODO change hardcoded limit
                    props["description"] = props["description"][:950] + "[...]"

            is_domain = BasePage(self.url).is_domain()
            if is_domain and ("thumbnail" not in props or props["thumbnail"] == None):
                if "favicons" in props:
                    favicons = props["favicons"]
                    if favicons and len(favicons) > 0:
                        props["thumbnail"] = favicons[0][0]

        # TODO
        # if "source" not in input_props:
        #    if not source_obj:
        #        input_props["source"] = p.get_domain()

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

        if not self.is_property_set(input_props, "source_obj") and not source_obj:
            input_props["source"] = self.url

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

        if type(p) is UrlHandler.youtube_video_handler:
            if not p.download_details():
                PersistentInfo.error(
                    "Could not obtain details for link:{}".format(url))

                return {}

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
        if not self.is_property_set(input_props, "artist"):
            input_props["artist"] = p.get_channel_name()
        if not self.is_property_set(input_props, "album"):
            input_props["album"] = p.get_channel_name()

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

        if url.startswith("http://"):
            url = url.replace("http://", "https://")

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
            input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if not self.is_property_set(input_props, "thumbnail"):
            input_props["thumbnail"] = p.get_thumbnail()

        if not self.is_property_set(input_props, "artist"):
            input_props["artist"] = p.get_domain()

        if not self.is_property_set(input_props, "album"):
            input_props["album"] = p.get_domain()

        input_props["page_rating_contents"] = p.get_page_rating()

        return input_props

    def get_rsspage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        if url.startswith("http://"):
            url = url.replace("http://", "https://")

        p = self.p

        if not p.is_valid():
            LinkDatabase.info("RSS page is invalid:{}".format(url))
            return

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
        if not self.is_property_set(input_props, "artist"):
            input_props["artist"] = p.get_domain()
        if not self.is_property_set(input_props, "album"):
            input_props["album"] = p.get_domain()
        if not self.is_property_set(input_props, "language"):
            input_props["language"] = None
        if not self.is_property_set(input_props, "title"):
            input_props["title"] = p.get_domain()
        if not self.is_property_set(input_props, "description"):
            input_props["description"] = p.get_domain()

        sources = SourceDataModel.objects.filter(url=input_props["source"])
        if sources.count() > 0:
            input_props["artist"] = sources[0].title
            input_props["album"] = sources[0].title

        return input_props

    def is_property_set(self, input_props, property):
        return property in input_props and input_props[property]


class UrlHandler(object):
    """
    Provides handler, controller for a link.
    The controller job is to provide usefull information about link.
    """

    youtube_video_handler = YouTubeVideoHandler
    youtube_channel_handler = YouTubeChannelHandler
    odysee_video_handler = OdyseeVideoHandler
    odysee_channel_handler = OdyseeChannelHandler

    def get(url, fast_check = True):
        url = UrlHandler.get_protololless(url)
        if not url:
            return

        if (
            url.startswith("www.youtube.com/watch")
            or url.startswith("youtube.com/watch")
            or url.startswith("m.youtube.com/watch")
            or (url.startswith("youtu.be/") and len(url) > len("youtu.be/"))
        ):
            return UrlHandler.youtube_video_handler(url)
        if (
            url.startswith("www.youtube.com/channel")
            or url.startswith("youtube.com/channel")
            or url.startswith("m.youtube.com/channel")
        ):
            return UrlHandler.youtube_channel_handler(url)
        if (
            url.startswith("www.youtube.com/feeds")
            or url.startswith("youtube.com/feeds")
            or url.startswith("m.youtube.com/feeds")
        ):
            return UrlHandler.youtube_channel_handler(url)
        if url.startswith("odysee.com/@"):
            wh1 = url.find("@")
            wh2 = url.find("/", wh1 + 1)
            if wh2 >= 0:
                return UrlHandler.odysee_video_handler(url)
        if url.startswith("odysee.com/@"):
            return UrlHandler.odysee_channel_handler(url)
        if url.startswith("odysee.com/$/rss"):
            return UrlHandler.odysee_channel_handler(url)

        from ..webtools import Url

        return Url.get(url, fast_check = fast_check)

    def get_protololless(url):
        if url.find("https://") >= 0:
            return url.replace("https://", "")
        if url.find("http://") >= 0:
            return url.replace("http://", "")

        if url.endswith("/"):
            url = url[:-1]
