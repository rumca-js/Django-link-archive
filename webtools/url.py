from urllib.parse import unquote
import urllib.robotparser
import asyncio

from .webtools import (
    RssPage,
    HtmlPage,
    DefaultContentPage,
    DomainAwarePage,
    ContentInterface,
    PageOptions,
    WebLogger,
    URL_TYPE_RSS,
    URL_TYPE_CSS,
    URL_TYPE_JAVASCRIPT,
    URL_TYPE_HTML,
    URL_TYPE_FONT,
    URL_TYPE_UNKNOWN,
)
from .handlerhttppage import (
    HttpPageHandler,
)

from .handlervideoyoutube import YouTubeJsonHandler
from .handlervideoodysee import OdyseeVideoHandler
from .handlerchannelyoutube import YouTubeChannelHandler
from .handlerchannelodysee import OdyseeChannelHandler

from utils.dateutils import DateUtils


class Url(ContentInterface):
    """
    Encapsulates data page, and builder to make request
    """

    youtube_video_handler = YouTubeJsonHandler
    youtube_channel_handler = YouTubeChannelHandler
    odysee_video_handler = OdyseeVideoHandler
    odysee_channel_handler = OdyseeChannelHandler

    def __init__(
        self, url=None, page_object=None, page_options=None, handler_class=None
    ):
        """
        @param handler_class Allows to enforce desired handler to be used to process link
        """
        if page_object:
            self.url = page_object.url
        else:
            self.url = url

        if page_options:
            self.options = page_options
        else:
            self.options = self.get_init_page_options(page_options)

        if handler_class:
            self.handler = handler_class(url, page_options=self.options)
        else:
            self.handler = None

        self.response = None
        self.contents = None

    def get_init_page_options(self, initial_options=None):
        options = PageOptions()

        if initial_options and initial_options.use_headless_browser:
            options.use_headless_browser = initial_options.use_headless_browser
        if initial_options and initial_options.use_full_browser:
            options.use_full_browser = initial_options.use_full_browser

        if Url.is_full_browser_required(self.url):
            options.use_full_browser = True
        if Url.is_headless_browser_required(self.url):
            options.use_headless_browser = True

        return options

    def get_contents(self):
        if self.contents:
            return self.contents

        self.handler = self.get_handler_implementation()
        if self.handler:
            self.contents = self.handler.get_contents()
            self.response = self.handler.get_response()

            return self.contents

    def get_response(self):
        if self.response:
            return self.response

        if not self.handler:
            self.handler = self.get_handler_implementation()

        if self.handler:
            self.response = self.handler.get_response()
            self.contents = self.handler.get_contents()

            if self.response:
                if not self.response.is_valid():
                    WebLogger.error(
                        "Url:{} Response is invalid:{}".format(self.url, self.response)
                    )

            return self.response

    def get_handlers():
        return [
           Url.youtube_video_handler,
           Url.youtube_channel_handler,
           Url.odysee_video_handler,
           Url.odysee_channel_handler,
        ]

    def get_handler(self):
        """
        This function does not fetch anything by itself
        """
        if self.handler:
            return self.handler

        self.handler = self.get_handler_implementation()
        return self.handler

    def get_type(url):
        """
        Based on link structure identify type.
        Should provide a faster means of obtaining handler, without the need
        to obtain the page

        TODO maybe we should 'ping page' to see status
        """
        # based on link 'appearance'

        if not url:
            return

        short_url = Url.get_protololless(url)
        if not short_url:
            return

        handlers = Url.get_handlers()
        for handler in handlers:
            if handler.is_handled_by(url):
                return handler(url)

        page_type = DomainAwarePage(url).get_type()

        # TODO this should return HttpPageHandler?

        if page_type == URL_TYPE_HTML:
            return HtmlPage(url, "")

        if page_type == URL_TYPE_RSS:
            return RssPage(url, "")

    def get_url_options(url):
        options = PageOptions()

        if Url.is_full_browser_required(url):
            options.use_full_browser = True
        elif Url.is_headless_browser_required(url):
            options.use_headless_browser = True

        p = DomainAwarePage(url)
        if p.is_link_service():
            options.link_redirect = True

        return options

    def get_handler_implementation(self):
        url = self.url
        if not url:
            return

        short_url = Url.get_protololless(url)

        if not short_url:
            return

        handlers = Url.get_handlers()
        for handler in handlers:
            if handler.is_handled_by(url):
                return handler(url)

        if url.startswith("https") or url.startswith("http"):
            return HttpPageHandler(url, page_options=self.options)
        elif url.startswith("smb") or url.startswith("ftp"):
            # not yet supported
            return DefaultContentPage(url)

    def is_url_valid(self):
        return True

    def is_domain(self):
        p = DomainAwarePage(self.url)
        return p.is_domain()

    def get_domain(self):
        if self.is_domain():
            return self
        else:
            p = DomainAwarePage(self.url)
            return Url(p.get_domain(), self.p.options)

    def get_robots_txt_url(self):
        return DomainAwarePage(self.url).get_robots_txt_url()

    def get_favicon(self):
        self.get_response()
        if not self.response:
            return

        if not self.url:
            return

        p = DomainAwarePage(self.url)
        if not p.is_web_link():
            return

        if self.handler:
            favicon = self.handler.get_favicon()
            if favicon:
                return favicon

        p = DomainAwarePage(self.url)
        if p.is_domain():
            return

        domain = p.get_domain()
        url = Url(domain)

        return url.get_favicon()

    def is_web_link(url):
        p = DomainAwarePage(url)
        return p.is_web_link()

    def get_cleaned_link(url):
        if not url:
            return

        if url.endswith("/"):
            url = url[:-1]
        if url.endswith("."):
            url = url[:-1]

        # domain is lowercase
        p = DomainAwarePage(url)
        domain = p.get_domain()
        if not domain:
            WebLogger.error("Could not obtain domain for:{}".format(url))
            return

        domain_lower = domain.lower()

        url = domain_lower + url[len(domain) :]

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

    def get_domain_info(self):
        return DomainCache.get_object(self.url)

    def download_all(url):
        from .programwrappers.wget import Wget

        wget = Wget(url)
        wget.download_all()

    def __str__(self):
        return "{}".format(self.options)

    def is_valid(self):
        if not self.handler:
            return False

        if not self.is_url_valid():
            return False

        if self.response is None:
            return False

        if self.response and not self.response.is_valid():
            return False

        if not self.handler.is_valid():
            return False

        return True

    def get_title(self):
        if self.handler:
            return self.handler.get_title()

    def get_description(self):
        if self.handler:
            return self.handler.get_description()

    def get_language(self):
        if self.handler:
            return self.handler.get_language()

    def get_thumbnail(self):
        if self.handler:
            return self.handler.get_thumbnail()

    def get_author(self):
        if self.handler:
            return self.handler.get_author()

    def get_album(self):
        if self.handler:
            return self.handler.get_album()

    def get_tags(self):
        if self.handler:
            return self.handler.get_tags()

    def get_date_published(self):
        if self.handler:
            return self.handler.get_date_published()

    def get_status_code(self):
        if self.response:
            return self.response.get_status_code()

        return 0

    def get_protololless(url):
        url = Url.get_cleaned_link(url)

        if not url:
            return

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

    def is_headless_browser_required(url):
        p = DomainAwarePage(url)

        require_headless_browser = [
            "open.spotify.com",
            "thehill.com",
        ]
        domain = p.get_domain_only()

        for rule in require_headless_browser:
            if domain.find(rule) >= 0:
                return True

        # to work around cookie banner requests
        if url.find("youtube.com/user/") >= 0 or url.find("youtube.com/channel/") >= 0:
            return True

        return False

    def is_full_browser_required(url):
        p = DomainAwarePage(url)
        if p.is_link_service():
            return True

        require_full_browser = [
            "defcon.org",
            "reuters.com",
            "yahoo.com",
            "techcrunch.com",
        ]
        domain = p.get_domain_only()

        for rule in require_full_browser:
            if domain.find(rule) >= 0:
                return True

        return False

    def get_entries(self):
        handler = self.get_handler()
        if handler:
            return handler.get_entries()


class DomainCacheInfo(object):
    """
    is_access_valid
    """

    def __init__(self, url, respect_robots_txt=True):
        p = DomainAwarePage(url)

        self.respect_robots_txt = respect_robots_txt

        self.url = p.get_domain()
        self.robots_contents = None

        if self.respect_robots_txt:
            self.robots_contents = self.get_robots_txt_contents()
            self.robots = self.get_robots_txt()

    def is_allowed(self, url):
        if self.respect_robots_txt and self.robots:
            user_agent = "*"
            return self.robots.can_fetch(user_agent, url)
        else:
            return True

    def get_robots_txt_url(self):
        p = DomainAwarePage(self.url)
        return p.get_robots_txt_url()

    def get_robots_txt(self):
        """
        https://developers.google.com/search/docs/crawling-indexing/robots/intro
        """
        contents = self.get_robots_txt_contents()
        if contents:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(self.get_robots_txt_url())
            rp.parse(contents.split("\n"))
            return rp

    def is_robots_txt(self):
        return self.get_robots_txt_contents()

    def get_robots_txt_contents(self):
        """
        We can only ask domain for robots
        """
        if self.robots_contents:
            return self.robots_contents

        robots_url = self.get_robots_txt_url()
        u = Url(robots_url)
        response = u.get_response()
        if response:
            self.robots_contents = response.get_text()

        return self.robots_contents

    def get_site_maps_urls(self):
        """
        https://stackoverflow.com/questions/2978144/pythons-robotparser-ignoring-sitemaps
        robot parser does not work. We have to do it manually
        """
        result = set()

        contents = self.get_robots_txt_contents()
        if contents:
            lines = contents.split("\n")
            for line in lines:
                line = line.replace("\r", "")
                wh = line.find("Sitemap")
                if wh >= 0:
                    wh2 = line.find(":")
                    if wh2 >= 0:
                        sitemap = line[wh2 + 1 :].strip()
                        result.add(sitemap)

        return list(result)

    def get_site_urls(self):
        result = []

        contents = self.get_robots_txt_contents()
        if contents:
            lines = contents.split("\n")
            for line in lines:
                if line.find("Disallow") >= 0 or line.find("Allow") >= 0:
                    link = process_allow_link(line)
                    result.append(link)

        urls = self.get_site_maps_urls()
        for url in urls:
            u = Url(url=url)
            response = u.get_response()
            contents = response.get_text()
            if contents:
                parser = ContentLinkParser(url, contents)
                parser = ContentLinkParser(self.url, contents)
                links = parser.get_links()

                result.extend(links)

        return result

    def process_allow_link(self, line):
        wh = line.find(":")
        if wh >= 0:
            part = line[wh + 1 :].strip()
            # robots can have wildcards, we cannot now what kind of location it is
            if part.find("*") == -1:
                return self.url + part

    def get_all_site_maps_urls(self):
        sites = set(self.get_site_maps_urls())

        for site in sites:
            subordinate_sites = self.get_subordinate_sites(site)
            sites.update(subordinate_sites)

        return list(sites)

    def get_subordinate_sites(self, site):
        all_subordinates = set()

        u = Url(site)
        response = u.get_response
        if not response:
            return all_subordinates

        contents = response.get_text()

        # check if it is sitemap / sitemap index
        # https://www.sitemaps.org/protocol.html#index
        if contents.find("<urlset") == -1 and contents.find("<sitemapindex") == -1:
            return all_subordinates

        p = ContentLinkParser(self.url, contents)
        links = p.get_links()

        for link in links:
            subordinates = self.get_subordinate_sites(link)
            all_subordinates.update(subordinates)

        return all_subordinates


class DomainCache(object):
    """
    DomainCache.get_object("https://youtube.com/mysite/something").is_allowed("url")
    Url().get_domain_cache().is_allowed()
    """

    object = None
    default_cache_size = 400  # 400 domains
    respect_robots_txt = True

    def get_object(domain_url):
        if DomainCache.object is None:
            DomainCache.object = DomainCache(
                DomainCache.default_cache_size, respect_robots_txt=True
            )

        return DomainCache.object.get_domain_info(domain_url)

    def __init__(self, cache_size=400, respect_robots_txt=True):
        """
        @note Not public
        """
        self.cache_size = cache_size
        self.cache = {}
        self.respect_robots_txt = respect_robots_txt

    def get_domain_info(self, input_url):
        domain_url = DomainAwarePage(input_url).get_domain_only()

        if not domain_url in self.cache:
            self.remove_from_cache()
            self.cache[domain_url] = {
                "date": DateUtils.get_datetime_now_utc(),
                "domain": self.read_info(domain_url),
            }

        return self.cache[domain_url]["domain"]

    def read_info(self, domain_url):
        return DomainCacheInfo(domain_url, self.respect_robots_txt)

    def remove_from_cache(self):
        if len(self.cache) < self.cache_size:
            return

        thelist = []
        for domain in self.cache:
            info = self.cache[domain]
            thelist.append([domain, info["date"], info["domain"]])

        thelist.sort(key=lambda x: x[1])
        thelist = thelist[-self.cache_size : -1]

        self.cache.clear()

        for item in thelist:
            self.cache[item[0]] = {"date": item[1], "domain": item[2]}


def fetch_url(link):
    u = Url(url = link)
    u.get_response()
    return u


async def fetch_all_urls(links, max_concurrency=10):
    num_pages = int(len(links) / max_concurrency)
    num_pages_mod = len(links) % max_concurrency

    if num_pages_mod != 0:
        num_pages += 1

    for num_page in range(num_pages):
        page_start = num_page * max_concurrency
        page_stop = page_start + max_concurrency

        tasks = []

        for link in links[page_start : page_stop]:
            tasks.append(asyncio.to_thread(fetch_url, link))

        result = await asyncio.gather(*tasks)
        return result
