import traceback
from urllib.parse import unquote

from ..webtools import Url, PageOptions, DomainAwarePage, DomainAwarePage

from ..apps import LinkDatabase
from ..models import AppLogging, EntryRule
from ..configuration import Configuration

from .handlervideoyoutube import YouTubeVideoHandler, YouTubeJsonHandler
from .handlervideoodysee import OdyseeVideoHandler

from .handlerchannelyoutube import YouTubeChannelHandler
from .handlerchannelodysee import OdyseeChannelHandler


class UrlHandler(Url):
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

    def __init__(self, url=None, page_object=None, page_options=None):
        super().__init__(url, page_object=page_object, page_options=page_options)

        if not url or url == "":
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            AppLogging.error(
                "Invalid use of UrlHandler API {};Lines:{}".format(url, line_text)
            )

            return

    def get_handler(self, url=None, page_object=None, page_options=None):
        """
        This code eventually will get ugly.
        We want handle different cases here. Use selenium?
        We do not want to handle that in web tools.
        """
        short_url = UrlHandler.get_protololless(url)
        if not short_url:
            return

        if UrlHandler.is_youtube_video(short_url):
            h = UrlHandler.youtube_video_handler(url)
            h.get_contents()
            self.response = h.response
            return h
        if UrlHandler.is_youtube_channel(short_url):
            h = UrlHandler.youtube_channel_handler(url)
            h.get_contents()
            self.response = h.response
            return h
        if UrlHandler.is_odysee_video(short_url):
            h = UrlHandler.odysee_video_handler(url)
            h.get_contents()
            self.response = h.response
            return h
        if UrlHandler.is_odysee_channel(short_url):
            h = UrlHandler.odysee_channel_handler(url)
            h.get_contents()
            self.response = h.response
            return h

        if not page_options:
            options = UrlHandler.get_url_options(url)
        else:
            options = page_options

        u = Url(url, page_options=options)
        if self.is_selenium_retry_possible(u, options):
            LinkDatabase.info(
                "Could not normally obtain contents. Trying selenium:".format(url)
            )

            options.use_selenium_headless = True

            if u.is_cloudflare_protected():
                options.link_redirect = True

            u = Url(url, page_options=options)

        self.options = u.options
        self.response = u.response
        return u.p

    def is_selenium_retry_possible(self, u, options):
        status_code = u.get_status_code()

        if status_code < 200 or status_code > 404:
            return False

        # if response is cloudflare jibberish, try using selenium
        # if page is invalid we may try with selenium. Some pages have cloudflare protection, or other
        if options.is_not_selenium() and (
            not u.is_valid or u.is_cloudflare_protected()
        ):
            return True
        return False

    def is_status_code_redirect(self, status_code):
        return (status_code >= 300 and status_code < 400) or status_code == 403

    def get_type(url):
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

        page = Url.get_type(url)
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
            or url.startswith("www.youtube.com/@")
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
        domain = DomainAwarePage(url).get_domain_only()

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
            or domain.find("yahoo.com") >= 0
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
        url = Url.get_cleaned_link(url)

        if url.startswith("https://") >= 0:
            return url.replace("https://", "")
        if url.startswith("http://") >= 0:
            return url.replace("http://", "")
        if url.startswith("ftp://") >= 0:
            return url.replace("ftp://", "")
        if url.startswith("smb://") >= 0:
            return url.replace("smb://", "")
        if url.startswith("//") >= 0:
            return url.replace("//", "")

    def get_cleaned_link(url):
        """
        TODO if possible should make translation between youtube -> canonical youtube link
        """

        url = Url.get_cleaned_link(url)

        stupid_google_string = "https://www.google.com/url"
        if url.find(stupid_google_string) >= 0:
            wh = url.find("http", len(stupid_google_string))
            if wh >= 0:
                url = url[wh:]
                wh = url.find("&")
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

    def is_valid(self):
        if not super().is_valid():
            return False

        if self.is_blocked():
            return False

        return True

    def is_blocked(self):
        keywords = Configuration.get_object().get_blocked_keywords()
        validator = UrlPropertyValidator(
            properties=self.get_properties(), blocked_keywords=keywords
        )
        if len(keywords) > 0:
            validator.blocked_keywords = keywords

        if not validator.is_valid():
            return True

        if not self.is_url_valid():
            return True

    def is_url_valid(self):
        if not super().is_url_valid():
            return False

        urls = EntryRule.get_blocked_urls()
        for url in urls:
            if self.url.find(url) >= 0:
                return False

        return True


class UrlPropertyValidator(object):
    def __init__(self, page_object=None, properties=None, blocked_keywords=None):
        self.properties = []
        if page_object:
            self.properties = page_object.get_properties()
        if properties:
            self.properties = properties

        if blocked_keywords and len(blocked_keywords) > 0:
            self.blocked_keywords = blocked_keywords
        else:
            self.blocked_keywords = [
                "masturbat",
                "porn",
                "xxx",
                "sex",
                "slutt",
                "nude",
                "chaturbat",
            ]

    def is_valid(self):
        if self.is_site_not_found():
            return False

        if self.is_porn_blocked():
            return False

        if self.is_casino_blocked():
            return False

        if self.is_blocked_keywords():
            return False

        return True

    def get_title(self):
        if "title" in self.properties:
            if self.properties["title"] is None:
                return ""
            return self.properties["title"]
        else:
            return ""

    def get_description(self):
        if "description" in self.properties:
            if self.properties["description"] is None:
                return ""
            return self.properties["description"]
        else:
            return ""

    def is_blocked_keywords(self):
        """
        TODO This should be configurable - move to configuration
        """
        title = self.get_title()
        title = title.lower()

        for keyword in self.blocked_keywords:
            if title.find(keyword) >= 0:
                return True

        return False

    def is_site_not_found(self):
        title = self.get_title()
        if title:
            title = title.lower()
        else:
            title = ""

        is_title_invalid = (
            title.find("forbidden") >= 0
            or title.find("access denied") >= 0
            or title.find("site not found") >= 0
            or title.find("page not found") >= 0
            or title.find("this page could not found") >= 0
            or title.find("404 not found") >= 0
            or title.find("404: not found") >= 0
            or title.find("404 not_found") >= 0
            or title.find("error 404") >= 0
            or title.find("404 error") >= 0
            or title.find("404 page") >= 0
            or title.find("404 file not found") >= 0
            or title.find("squarespace - website expired") >= 0
            or title.find("domain name for sale") >= 0
            or title.find("account suspended") >= 0
            or title.find("the request could not be satisfied") >= 0
        )

        if is_title_invalid:
            LinkDatabase.info("Title is invalid {}".format(title))
            return True

    def is_porn_blocked(self):
        """
        TODO This should be configurable - move to configuration
        """
        title = self.get_title()
        title = title.lower()

        porn_keywords = [
            "masturbat",
            "porn",
            "xxx",
            "sex",
            "slutt",
            "nude",
            "chaturbat",
        ]

        for keyword in porn_keywords:
            if title.find(keyword) >= 0:
                return True

        keywords = [
            "live",
            "nast",
            "slut",
            "webcam",
        ]

        points = 0
        for keyword in keywords:
            if title.find(keyword) >= 0:
                points += 1

        return points > 3

    def is_casino_blocked(self):
        """
        TODO This should be configurable - move to configuration
        """
        title = self.get_title()
        title = title.lower()

        if title.find("slot server") >= 0:
            return True

        description = self.get_description()
        description = description.lower()

        text = title + "\n" + description

        keywords = ["casino", "lotter", "bingo", "slot", "poker", "jackpot", "gacor"]

        sum = 0
        for keyword in keywords:
            sum += text.count(keyword)

        return sum > 3
