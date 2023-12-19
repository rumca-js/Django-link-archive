from ..webtools import HtmlPage, RssPage
from ..dateutils import DateUtils
from ..controllers import SourceDataController

from ..apps import LinkDatabase


class YouTubeException(Exception):
    pass


class HandlerUrl(object):
    def __init__(self, url):
        self.url = url

        if self.url.endswith("/"):
            self.url = self.url[:-1]

        from ..pluginentries.handlervideoyoutube import YouTubeVideoHandler

        self.youtube_video_handler = YouTubeVideoHandler

    def get_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        props = self.get_props_implementation(input_props)

        if props:
            if "description" in props:
                # TODO change hardcoded limit
                props["description"] = props["description"][:900]

        # TODO
        # if "source" not in input_props:
        #    if not source_obj:
        #        input_props["source"] = p.get_domain()

        return props

    def get_props_implementation(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        p = HtmlPage(self.url)

        if "source" not in input_props:
            if source_obj:
                input_props["source"] = source_obj.url

        if p.is_domain():
            input_props["permanent"] = True
            input_props["bookmarked"] = False

        if "source_obj" not in input_props and source_obj:
            input_props["source_obj"] = source_obj

        if "source" not in input_props and source_obj:
            input_props["source"] = source_obj.url

        if p.is_youtube():
            handler = self.youtube_video_handler(self.url)
            if handler.get_video_code():
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

        h = self.youtube_video_handler(url)
        if not h.download_details():
            raise YouTubeException("Could not obtain details for link:{}".format(url))

        source_url = h.get_channel_feed_url()
        if source_url is None:
            raise YouTubeException(
                "Could not obtain channel feed url:{}".format(source_url)
            )

        sources = SourceDataController.objects.filter(url=source_url)
        if sources.exists():
            source_obj = sources[0]

        if "link" not in input_props:
            input_props["link"] = h.get_link_url()
        if "title" not in input_props:
            input_props["title"] = h.get_title()
        if "description" not in input_props:
            input_props["description"] = h.get_description()
        if "date_published" not in input_props:
            input_props["date_published"] = h.get_datetime_published()
        if "thumbnail" not in input_props:
            input_props["thumbnail"] = h.get_thumbnail()
        if "artist" not in input_props:
            input_props["artist"] = h.get_channel_name()
        if "album" not in input_props:
            input_props["album"] = h.get_channel_name()

        if "language" not in input_props and source_obj:
            input_props["language"] = source_obj.language

        if "source" not in input_props and source_obj:
            input_props["source"] = source_obj.url

        return input_props

    def get_htmlpage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        if url.startswith("http://"):
            url = url.replace("http://", "https://")

        p = HtmlPage(url)

        # some pages return invalid code / information. let the user decide
        # what to do about it

        if "link" not in input_props:
            input_props["link"] = p.url
        if "title" not in input_props:
            title = p.get_title()
            input_props["title"] = title
        if "description" not in input_props:
            description = p.get_description()
            if description is None:
                description = title
            input_props["description"] = description

        if "language" not in input_props:
            language = p.get_language()
            if not language:
                if source_obj:
                    language = source_obj.language
            input_props["language"] = language

        if "date_published" not in input_props:
            input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if "thumbnail" not in input_props:
            input_props["thumbnail"] = p.get_thumbnail()

        if "artist" not in input_props:
            input_props["artist"] = p.get_domain()

        if "album" not in input_props:
            input_props["album"] = p.get_domain()

        if "source" not in input_props:
            if source_obj:
                input_props["source"] = source_obj.url
            else:
                input_props["source"] = p.get_domain()

        input_props["page_rating_contents"] = p.get_page_rating()

        return input_props

    def get_rsspage_props(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url

        if url.startswith("http://"):
            url = url.replace("http://", "https://")

        link_page = RssPage(url)

        if not link_page.is_valid():
            LinkDatabase.info("RSS page is invalid:{}".format(url))
            return

        if "link" not in input_props:
            input_props["link"] = link_page.url
        if "title" not in input_props:
            title = link_page.get_title()
            input_props["title"] = title
        if "description" not in input_props:
            description = link_page.get_description()
            if description is None:
                description = title
            input_props["description"] = description

        if "language" not in input_props:
            language = link_page.get_language()
            if not language:
                if source_obj:
                    language = source_obj.language
            input_props["language"] = language

        if "date_published" not in input_props:
            input_props["date_published"] = DateUtils.get_datetime_now_utc()

        if "thumbnail" not in input_props:
            input_props["thumbnail"] = link_page.get_thumbnail()

        input_props["page_rating_contents"] = link_page.get_page_rating()

        return input_props

    def update_info_default(self, input_props=None, source_obj=None):
        if not input_props:
            input_props = {}

        url = self.url
        p = HtmlPage(url)

        if not p.is_valid():
            LinkDatabase.info("HTML page is invalid:{}".format(url))
            return

        if "source" not in input_props or not input_props["source"]:
            input_props["source"] = p.get_domain()
        if "artist" not in input_props or not input_props["artist"]:
            input_props["artist"] = p.get_domain()
        if "album" not in input_props or not input_props["album"]:
            input_props["album"] = p.get_domain()
        if "language" not in input_props or not input_props["language"]:
            input_props["language"] = ""
        if "title" not in input_props or not input_props["title"]:
            input_props["title"] = p.get_domain()
        if "description" not in input_props or not input_props["description"]:
            input_props["description"] = p.get_domain()

        sources = SourceDataModel.objects.filter(url=input_props["source"])
        if sources.count() > 0:
            input_props["artist"] = sources[0].title
            input_props["album"] = sources[0].title

        return input_props


class NewHandlerUrl(object):
    def get(url):
        if url == "https://youtube.com/watch":
            return YouTubeVideoHandler(url)
        if url == "https://www.youtube.com/channel":
            return YouTubeSourceHandler(url)
        if url == "https://www.youtube.com/feeds":
            return YouTubeSourceHandler(url)
        # TODO implement check below
        if url == "https://odysee.com/user/video":
            return OdyseeVideoHandler(url)
        # TODO implement check below
        if url == "https://odysee.com/user/":
            return OdyseeSourceHandler(url)
        if url == "https://odysee.com/$/rss":
            return OdyseeSourceHandler(url)

        from ..webtools import Url
        return Url(url)
