import traceback

from ..webtools import Url, PageOptions, DomainAwarePage, BasePage

from ..apps import LinkDatabase
from ..models import AppLogging

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

    def get(url, fast_check=True, use_selenium=False, page_options=None):
        if not url or url == "":
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            AppLogging.error(
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

        if not page_options:
            options = UrlHandler.get_url_options(url)
            if options.is_not_selenium() and use_selenium:
                options.use_selenium_headless = True
            options.fast_parsing = fast_check
        else:
            options = page_options

        page = Url.get(url, options=options)

        # if response is cloudflare jibberish, try using selenium
        if options.is_not_selenium() and (
            (not page.is_valid() or page.is_cloudflare_protected())
            or (page.status_code == 403)
        ):
            LinkDatabase.info(
                "Could not normally obtain contents. Trying selenium:".format(url)
            )

            options = PageOptions()
            # by default we do not want full blown browser to be started
            # this has to be enabled manually in code
            options.use_selenium_headless = True
            options.fast_parsing = fast_check

            if page.is_cloudflare_protected():
                options.link_redirect = True

            page = Url.get(url, options=options)

        return page

    def get_type(url, fast_check=True):
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

        options = PageOptions()
        options.fast_parsing = fast_check

        page = Url.get(url, options=options)
        return page

    def get_url_options(url):
        options = PageOptions()

        if UrlHandler.is_selenium_full_required(url):
            options.use_selenium_full = True
        if UrlHandler.is_selenium_headless_required(url):
            options.use_selenium_headless = True

        p = DomainAwarePage(url)
        if p.is_link_service():
            options.link_redirect = True

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
        domain = BasePage(url).get_domain_only()

        if domain.startswith("open.spotify.com") or domain.startswith("thehill.com"):
            return True

        return False

    def is_selenium_full_required(url):
        p = DomainAwarePage(url)
        domain = p.get_domain_only()

        if (
            p.is_link_service()
            or domain.startswith("www.warhammer-community.com")
            or domain.startswith("defcon.org")
        ):
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

    def get_cleaned_link(url):
        """
        TODO if possible should make translation between youtube -> canonical youtube link
        """
        from urllib.parse import unquote

        url = Url.get_cleaned_link(url)

        stupid_google_string = "https://www.google.com/url?q="
        if url.find(stupid_google_string) >= 0:
            wh = url.find("http", len(stupid_google_string))
            if wh >= 0:
                url = url[wh:]
                wh = url.find("&sa=U")
                if wh >= 0:
                    url = url[:wh]
                    url = Url.get_cleaned_link(url)

        stupid_youtube_string = "https://www.youtube.com/redirect"
        if url.find(stupid_youtube_string) >= 0:
            wh = url.rfind("&q=")
            if wh >= 0:
                wh = url.find("http", wh)
                if wh >= 0:
                    url = url[wh:]
                    url = unquote(url)
                    url = Url.get_cleaned_link(url)

        return url
