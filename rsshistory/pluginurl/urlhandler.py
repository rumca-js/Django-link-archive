import traceback

from ..webtools import Url, PageOptions, DomainAwarePage

from ..apps import LinkDatabase
from ..models import PersistentInfo

from .handlervideoyoutube import YouTubeVideoHandler, YouTubeJsonHandler
from .handlervideoodysee import OdyseeVideoHandler

from .handlerchannelyoutube import YouTubeChannelHandler
from .handlerchannelodysee import OdyseeChannelHandler


class UrlHandler(object):
    """
    Provides handler, controller for a link. Should inherit title & description API, just like
    webtools Url.

    You can extend it, provide more handlers.

    The controller job is to provide usefull information about link.
    """

    youtube_video_handler = YouTubeJsonHandler
    youtube_channel_handler = YouTubeChannelHandler
    odysee_video_handler = OdyseeVideoHandler
    odysee_channel_handler = OdyseeChannelHandler

    def get(url, fast_check=True, use_selenium=False):
        if not url or url == "":
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            PersistentInfo.error(
                "Invalid use of UrlHandler API {};Lines:{}".format(url, line_text)
            )

            return

        """
        This code eventually will get ugly.
        We want handle different cases here. Use selenium?
        We do not want to handle that in web tools.
        """
        short_url = UrlHandler.get_protololless(url)
        if not short_url:
            return

        if UrlHandler.is_youtube_video(short_url):
            return UrlHandler.youtube_video_handler(url)
        if UrlHandler.is_youtube_channel(short_url):
            return UrlHandler.youtube_channel_handler(url)
        if UrlHandler.is_odysee_video(short_url):
            return UrlHandler.odysee_video_handler(url)
        if UrlHandler.is_odysee_channel(short_url):
            return UrlHandler.odysee_channel_handler(url)

        options = UrlHandler.get_url_options(url)
        if options.is_not_selenium() and use_selenium:
            options.use_selenium_headless = True
        options.fast_parsing = fast_check

        page = Url.get(url, options=options)

        # if response is cloudflare jibberish, try using selenium
        if options.is_not_selenium() and (not page.is_valid() or page.is_cloudflare_protected()):
            LinkDatabase.info("Could not normally obtain contents. Trying selenium:".format(url))

            options = PageOptions()
            # by default we do not want full blown browser to be started
            # this has to be enabled manually in code
            options.use_selenium_headless = True
            options.fast_parsing = fast_check

            page = Url.get(url, options=options)

        return page

    def get_url_options(url):
        options = PageOptions()

        if UrlHandler.is_selenium_full_required(url):
            options.use_selenium_full = True
        if UrlHandler.is_selenium_headless_required(url):
            options.use_selenium_headless = True

        return options

    def is_youtube_video(url):
        return (
            url.startswith("www.youtube.com/watch")
            or url.startswith("youtube.com/watch")
            or url.startswith("m.youtube.com/watch")
            or (url.startswith("youtu.be/") and len(url) > len("youtu.be/"))
        )

    def is_youtube_channel(url):
        if (
            url.startswith("www.youtube.com/channel")
            or url.startswith("youtube.com/channel")
            or url.startswith("m.youtube.com/channel")
        ):
            return True
        if (
            url.startswith("www.youtube.com/feeds")
            or url.startswith("youtube.com/feeds")
            or url.startswith("m.youtube.com/feeds")
        ):
            return True

    def is_odysee_video(url):
        if url.startswith("odysee.com/@"):
            wh1 = url.find("@")
            wh2 = url.find("/", wh1 + 1)
            if wh2 >= 0:
                return True

    def is_odysee_channel(url):
        if url.startswith("odysee.com/@"):
            return True
        if url.startswith("odysee.com/$/rss"):
            return True

    def is_selenium_headless_required(url):
        if (
            url.startswith("https://open.spotify.com")
            or url.startswith("https://thehill.com")
        ):
            return True

        return False

    def is_selenium_full_required(url):
        p = DomainAwarePage(url)
        if (p.is_link_service() or
            url.startswith("https://www.warhammer-community.com") or
            url.startswith("https://defcon.org")):
            return True

        return False

    def get_page_options(url):
        o = PageOptions()

        if UrlHandler.is_selenium_full_required(url):
            o.use_selenium_full = True
        if UrlHandler.is_selenium_headless_required(url):
            o.use_selenium_headless = True

        return o

    def get_protololless(url):
        if url.find("https://") >= 0:
            return url.replace("https://", "")
        if url.find("http://") >= 0:
            return url.replace("http://", "")

        if url.endswith("/"):
            url = url[:-1]
