"""
Main Url handling class

@example
url = Url(link = "https://google.com")
response = url.get_response()

options.request.url
options.mode_mapping

"""

from urllib.parse import unquote, urlparse, parse_qs
from collections import OrderedDict
import urllib.robotparser
import asyncio
import base64

from .webtools import (
    PageOptions,
    WebLogger,
    URL_TYPE_RSS,
    URL_TYPE_CSS,
    URL_TYPE_JAVASCRIPT,
    URL_TYPE_HTML,
    URL_TYPE_FONT,
    URL_TYPE_UNKNOWN,
    status_code_to_text,
)
from .webconfig import WebConfig
from .urllocation import UrlLocation
from .pages import (
    ContentInterface,
    DefaultContentPage,
    RssPage,
    HtmlPage,
)
from .crawlers import (
    RequestsCrawler,
)

from .handlers import (
    YouTubeJsonHandler,
    OdyseeVideoHandler,
    YouTubeChannelHandler,
    OdyseeChannelHandler,
    RedditUrlHandler,
    ReturnDislike,
    GitHubUrlHandler,
    HackerNewsHandler,
    InternetArchive,
    FourChanChannelHandler,
    TwitterUrlHandler,
    HttpPageHandler,
)

from utils.dateutils import DateUtils


class Url(ContentInterface):
    """
    Encapsulates data page, and builder to make request
    """

    youtube_video_handler = YouTubeJsonHandler
    youtube_channel_handler = YouTubeChannelHandler
    odysee_video_handler = OdyseeVideoHandler
    odysee_channel_handler = OdyseeChannelHandler

    handlers = [
        YouTubeJsonHandler,
        YouTubeChannelHandler,
        OdyseeVideoHandler,
        OdyseeChannelHandler,
        RedditUrlHandler,
        ReturnDislike,
        GitHubUrlHandler,
        HackerNewsHandler,
        InternetArchive,
        FourChanChannelHandler,
        TwitterUrlHandler,
        HttpPageHandler,  # default
    ]

    def __init__(self, url=None, settings=None, url_builder=None):
        """
        @param handler_class Allows to enforce desired handler to be used to process link

        There are various ways url can be specified. For simplicity we cleanup it.
        I do not like trailing slashes, no google stupid links, etc.
        """

        if url:
            self.request_url = url
            url = Url.get_cleaned_link(url)
            self.url = url
        else:
            self.url = None
            self.request_url = None

        self.settings = settings
        self.handler = None

        if not self.settings:
            self.settings = WebConfig.get_default_crawler(self.url)

        if "crawler" not in self.settings:
            settings = WebConfig.get_default_crawler(self.url)

            self.settings["name"] = settings["name"]
            self.settings["crawler"] = settings["crawler"]
            self.settings["settings"] = settings["settings"]

        if self.settings and "handler_class" in self.settings:
            handler_class = self.settings["handler_class"]
            self.handler = handler_class(
                url=self.url, settings=self.settings, url_builder=url_builder
            )

        self.response = None
        self.url_builder = url_builder
        if not self.url_builder:
            self.url_builder = Url

    def get_init_settings(self):
        return WebConfig.get_default_crawler(self.url)

    def get_handlers():
        return Url.handlers

    def register(handler):
        Url.handlers.append(handler)

    def get_handler_by_name(handler_name):
        handlers = Url.get_handlers()
        for handler in handlers:
            if handler.__name__ == handler_name:
                return handler

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

        p = UrlLocation(url)
        short_url = p.get_protocolless()
        if not short_url:
            return

        handlers = Url.get_handlers()
        for handler in handlers:
            if handler(url).is_handled_by():
                if handler == HttpPageHandler:
                    page_type = UrlLocation(url).get_type()

                    # TODO this should return HttpPageHandler?

                    if page_type == URL_TYPE_HTML:
                        return HtmlPage(url, "")

                    if page_type == URL_TYPE_RSS:
                        return RssPage(url, "")

                    if url.find("rss") >= 0:
                        return RssPage(url, "")
                    if url.find("feed") >= 0:
                        return RssPage(url, "")

                    return

                return handler(url)

    def get_contents(self):
        """
        Returns text
        """
        if self.response:
            return self.response.get_text()

        if not self.handler:
            self.handler = self.get_handler_implementation()

        if self.handler:
            self.response = self.handler.get_response()
            if self.response:
                return self.response.get_text()

    def get_binary(self):
        """
        Returns text
        """
        if self.response:
            return self.response.get_binary()

        if not self.handler:
            self.handler = self.get_handler_implementation()

        if self.handler:
            self.response = self.handler.get_response()

            if self.response:
                return self.response.get_binary()

    def get_response(self):
        """
        Returns full response, with page handling object
        """
        if self.response:
            return self.response

        if not self.handler:
            self.handler = self.get_handler_implementation()

        if self.handler:
            if (
                "respect_robots_txt" in self.settings
                and self.settings["respect_robots_txt"]
            ):
                if not self.is_allowed():
                    return

            self.response = self.handler.get_response()

            if self.response:
                if not self.response.is_valid():
                    WebLogger.error(
                        "Url:{} Response is invalid:{}".format(self.url, self.response)
                    )

            return self.response

    def get_headers(self):
        # TODO implement
        pass

    def ping(self, timeout_s=20, user_agent=None):
        return RequestsCrawler.ping(
            self.url, timeout_s=timeout_s, user_agent=user_agent
        )

    def get_handler_implementation(self):
        url = self.url
        if not url:
            return

        p = UrlLocation(url)
        short_url = p.get_protocolless()

        if not short_url:
            return

        handlers = Url.get_handlers()
        for handler in handlers:
            h = handler(
                url=self.url, settings=self.settings, url_builder=self.url_builder
            )
            if h.is_handled_by():
                self.url = h.url
                return h

        if url.startswith("https") or url.startswith("http"):
            return HttpPageHandler(
                url=url, settings=self.settings, url_builder=self.url_builder
            )
        elif url.startswith("smb") or url.startswith("ftp"):
            raise NotImplementedError("Protocol has not been implemented")

    def is_url_valid(self):
        return True

    def is_domain(self):
        p = UrlLocation(self.url)
        return p.is_domain()

    def get_domain(self):
        if self.is_domain():
            return self
        else:
            p = UrlLocation(self.url)
            u = self.url_builder(p.get_domain())
            u.set_config(self.settings)
            return u

    def get_robots_txt_url(self):
        return UrlLocation(self.url).get_robots_txt_url()

    def get_favicon(self):
        self.get_response()
        if not self.response:
            return

        if not self.url:
            return

        p = UrlLocation(self.url)
        if not p.is_web_link():
            return

        if self.handler:
            favicon = self.handler.get_favicon()
            if favicon:
                return favicon

        p = UrlLocation(self.url)
        if p.is_domain():
            return

        domain = p.get_domain()

        url = self.url_builder(domain)
        url.set_config(self.settings)

        return url.get_favicon()

    def is_web_link(url):
        p = UrlLocation(url)
        return p.is_web_link()

    def is_protocolled_link(url):
        p = UrlLocation(url)
        return p.is_protocolled_link()

    def get_cleaned_link(url):
        if not url:
            return

        url = url.strip()

        if url.endswith("/"):
            url = url[:-1]
        if url.endswith("."):
            url = url[:-1]

        # domain is lowercase
        p = UrlLocation(url)
        domain = p.get_domain()
        if not domain:
            WebLogger.error("Could not obtain domain for:{}".format(url))
            return

        domain_lower = domain.lower()

        url = domain_lower + url[len(domain) :]

        stupid_google_string = "https://www.google.com/url"
        if url.find(stupid_google_string) >= 0:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            param_value = query_params.get("url", [None])[0]
            if param_value:
                return param_value
            param_value = query_params.get("q", [None])[0]
            if param_value:
                return param_value

        stupid_youtube_string = "https://www.youtube.com/redirect"
        if url.find(stupid_youtube_string) >= 0:
            parsed_url = urlparse(url)
            query_params = parse_qs(parsed_url.query)
            param_value = query_params.get("q", [None])[0]

            param_value = unquote(param_value)
            param_value = Url.get_cleaned_link(param_value)
            return param_value

        return url

    def get_clean_url(self):
        self.get_handler()
        if self.handler:
            return self.handler.get_url()
        else:
            return self.url

    def get_canonical_url(self):
        if self.handler:
            return self.handler.get_canonical_url()

        handlers = Url.get_handlers()
        for handler_class in handlers:
            handler = handler_class(url=self.url)
            if handler.is_handled_by():
                return handler.get_canonical_url()

        return self.url

    def get_urls(self):
        properties = {}
        properties["link"] = self.url
        properties["link_request"] = self.request_url
        properties["link_canonical"] = self.get_canonical_url()
        return properties

    def get_urls_archive(self):
        p = UrlLocation(self.url)
        short_url = p.get_protocolless()

        properties = []

        archive = InternetArchive(self.url)
        properties.append(archive.get_archive_url())

        properties.append("https://archive.ph/" + short_url)

        return properties

    def get_domain_info(self):
        return DomainCache.get_object(self.url)

    def __str__(self):
        return "{}".format(self.settings)

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

    def is_selenium_browser_required(url):
        if not url:
            return False

        p = UrlLocation(url)

        require_headless_browser = [
            "open.spotify.com",
        ]
        domain = p.get_domain_only()

        for rule in require_headless_browser:
            if domain.find(rule) >= 0:
                return True

        # to work around cookie banner requests
        if url.find("youtube.com/user/") >= 0 or url.find("youtube.com/channel/") >= 0:
            return True
        if url.find("youtube.com/@") >= 0:
            return True

        return False

    def is_crawlee_browser_required(url):
        if not url:
            return False

        p = UrlLocation(url)
        if p.is_link_service():
            return True

        require_full_browser = [
            "defcon.org",
            "reuters.com",
            "yahoo.com",
            "techcrunch.com",
            "thehill.com",
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
        else:
            return []

    def find_rss_url(url):
        """
        @param url needs to be Url object
        """
        if not url:
            return

        handler = url.get_handler()
        if not handler:
            return

        # maybe our handler is able to produce feed without asking for response

        feeds = url.get_feeds()
        if url.url in feeds:
            return url

        if feeds and len(feeds) > 0:
            u = url.url_builder(url=feeds[0])
            return u

        # obtain response?
        handler.get_response()

        if type(handler) is HttpPageHandler:
            if type(handler.p) is RssPage:
                return url

        # try again to obtain feed

        feeds = url.get_feeds()
        if url.url in feeds:
            return url

        if feeds and len(feeds) > 0:
            u = url.url_builder(url=feeds[0])
            return u

    def get_feeds(self):
        result = []

        handler = self.get_handler()
        if handler:
            return handler.get_feeds()

        return result

    def get_contents_hash(self):
        handler = self.get_handler()
        if handler:
            return handler.get_contents_hash()

    def get_contents_body_hash(self):
        handler = self.get_handler()
        if handler:
            return handler.get_contents_body_hash()

    def get_properties(self, full=False, include_social=False, check_robots=False):
        basic_properties = super().get_properties()
        basic_properties["link_request"] = self.request_url

        if not full:
            return basic_properties

        response = self.get_response()
        page_handler = self.get_handler()

        all_properties = []

        properties_data = self.get_properties_data()

        all_properties.append({"name": "Properties", "data": properties_data})

        if response:
            if response.get_text():
                all_properties.append(
                    {"name": "Text", "data": {"Contents": response.get_text()}}
                )
            elif response.get_binary():
                all_properties.append(
                    {
                        "name": "Binary",
                        "data": {
                            "Contents": self.property_encode(response.get_binary())
                        },
                    }
                )

        request_data = dict(self.settings)
        request_data["crawler"] = type(request_data["crawler"]).__name__

        all_properties.append({"name": "Settings", "data": request_data})

        response_data = self.get_response_data()
        all_properties.append({"name": "Response", "data": response_data})
        raw_headers_data = response.get_headers()
        all_properties.append({"name": "Headers", "data": raw_headers_data})

        if include_social:
            social_data = self.get_social_properties(self.url)
            if social_data:
                all_properties.append({"name": "Social", "data": social_data})

        entries_data = self.get_entry_data()
        all_properties.append({"name": "Entries", "data": entries_data})

        return all_properties

    def get_properties_data(self):
        properties = super().get_properties()
        response = self.get_response()
        page_handler = self.get_handler()

        properties["link_request"] = self.request_url

        feeds = self.get_feeds()
        if len(feeds) > 0:
            properties["feeds"] = []
            for key, feed in enumerate(feeds):
                properties["feeds"].append(feed)

        if type(page_handler) is Url.youtube_channel_handler:
            if page_handler.get_channel_name():
                properties["channel_name"] = page_handler.get_channel_name()
                properties["channel_url"] = page_handler.get_channel_url()

        if type(page_handler) is Url.youtube_video_handler:
            if page_handler.get_channel_name():
                properties["channel_name"] = page_handler.get_channel_name()
                properties["channel_url"] = page_handler.get_channel_url()

        if type(page_handler) is HttpPageHandler and type(page_handler.p) is HtmlPage:
            properties["favicon"] = page_handler.p.get_favicon()
            properties["meta title"] = page_handler.p.get_meta_field("title")
            properties["meta description"] = page_handler.p.get_meta_field(
                "description"
            )
            properties["meta keywords"] = page_handler.p.get_meta_field("keywords")

            properties["og:title"] = page_handler.p.get_og_field("title")
            properties["og:description"] = page_handler.p.get_og_field("description")
            properties["og:image"] = page_handler.p.get_og_field("image")
            properties["og:site_name"] = page_handler.p.get_og_field("site_name")
            properties["schema:thumbnailUrl"] = page_handler.p.get_schema_field(
                "thumbnailUrl"
            )

        properties["link_archives"] = self.get_urls_archive()

        return properties

    def get_response_data(self):
        """
        Easy digestible response data
        """
        response_data = OrderedDict()
        response = self.get_response()
        page_handler = self.get_handler()

        response_data["is_valid"] = response.is_valid()

        respect_robots_txt = False
        is_allowed = True
        if (
            "respect_robots_txt" in self.settings
            and self.settings["respect_robots_txt"]
        ):
            respect_robots_txt = self.settings["respect_robots_txt"]
            is_allowed = self.is_allowed()

        response_data["is_allowed"] = is_allowed
        if respect_robots_txt and not is_allowed:
            return response_data

        if response:
            response_data["status_code"] = response.get_status_code()
            response_data["status_code_str"] = status_code_to_text(
                response.get_status_code()
            )

            response_data["crawl_time_s"] = response.crawl_time_s

            response_data["Content-Type"] = response.get_content_type()
            if page_handler == HttpPageHandler:
                if page_handler.p:
                    if type(page_handler.p) == RssPage:
                        response_data["Content-Type"] = "application/rss+xml"
                    if type(page_handler.p) == HtmlPage:
                        response_data["Content-Type"] = "text/html"

            response_data["Content-Length"] = response.get_content_length()
            response_data["Last-Modified"] = response.get_last_modified()
            response_data["Charset"] = response.get_encoding()
            if not response_data["Charset"]:
                response_data["Charset"] = response.encoding

            if self.get_contents_hash():
                response_data["hash"] = self.property_encode(self.get_contents_hash())
            else:
                response_data["hash"] = ""
            if self.get_contents_body_hash():
                response_data["body_hash"] = self.property_encode(
                    self.get_contents_body_hash()
                )
            else:
                response_data["body_hash"] = ""

            if len(response.errors) > 0:
                response_data["errors"] = []
                for error in response.errors:
                    response_data["errors"].append(error)

        return response_data

    def get_entry_data(self):
        index = 0
        entries = []
        for entry in self.get_entries():
            if "feed_entry" in entry:
                del entry["feed_entry"]
            entries.append(entry)

        return entries

    def property_encode(self, byte_property):
        return base64.b64encode(byte_property).decode("utf-8")

    def is_allowed(self):
        domain_info = self.get_domain_info()
        return domain_info.is_allowed(self.url)

    def get_social_properties(self):
        url = self.url

        json_obj = {}

        json_obj["thumbs_up"] = None
        json_obj["thumbs_down"] = None
        json_obj["view_count"] = None
        json_obj["rating"] = None
        json_obj["upvote_ratio"] = None
        json_obj["upvote_view_ratio"] = None

        handler = self.get_handler()
        if not handler:
            return json_obj

        json_obj = handler.get_json_data()
        if not json_obj:
            json_obj = {}
            if "thumbs_up" not in json_obj:
                json_obj["thumbs_up"] = None
            if "thumbs_down" not in json_obj:
                json_obj["thumbs_down"] = None
            if "view_count" not in json_obj:
                json_obj["view_count"] = None
            if "rating" not in json_obj:
                json_obj["rating"] = None
            if "upvote_ratio" not in json_obj:
                json_obj["upvote_ratio"] = None
            if "upvote_view_ratio" not in json_obj:
                json_obj["upvote_view_ratio"] = None
            return json_obj

        if "thumbs_up" not in json_obj:
            json_obj["thumbs_up"] = None
        if "thumbs_down" not in json_obj:
            json_obj["thumbs_down"] = None
        if "view_count" not in json_obj:
            json_obj["view_count"] = None
        if "rating" not in json_obj:
            json_obj["rating"] = None
        if "upvote_ratio" not in json_obj:
            json_obj["upvote_ratio"] = None
        if "upvote_view_ratio" not in json_obj:
            json_obj["upvote_view_ratio"] = None

        return json_obj


class DomainCacheInfo(object):
    """
    is_access_valid
    """

    def __init__(self, url, respect_robots_txt=True, settings=None, url_builder=None):
        p = UrlLocation(url)

        self.respect_robots_txt = respect_robots_txt

        self.url = p.get_domain()
        self.robots_contents = None
        self.settings = settings
        self.url_builder = url_builder

        if not self.url_builder:
            self.url_builder = Url

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
        p = UrlLocation(self.url)
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
        u = self.url_builder(robots_url, settings=self.settings)

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
            u = slef.url_builder(url=url)
            u.set_config(self.settings)
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

        u = self.url_builder(site)
        u.set_config(self.settings)
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

    object = None  # singleton
    default_cache_size = 400
    respect_robots_txt = True

    def get_object(domain_url, settings=None, url_builder=None):
        if DomainCache.object is None:
            DomainCache.object = DomainCache(
                DomainCache.default_cache_size,
                settings=settings,
                url_builder=url_builder,
            )

        return DomainCache.object.get_domain_info(domain_url)

    def __init__(
        self,
        cache_size=400,
        respect_robots_txt=True,
        settings=None,
        url_builder=None,
    ):
        """
        @note Not public
        """
        self.cache_size = cache_size
        self.cache = {}
        self.respect_robots_txt = respect_robots_txt
        self.settings = settings
        self.url_builder = url_builder

    def get_domain_info(self, input_url):
        domain_url = UrlLocation(input_url).get_domain_only()

        if not domain_url in self.cache:
            self.remove_from_cache()
            self.cache[domain_url] = {
                "date": DateUtils.get_datetime_now_utc(),
                "domain": self.read_info(domain_url),
            }

        return self.cache[domain_url]["domain"]

    def read_info(self, domain_url):
        return DomainCacheInfo(
            domain_url,
            self.respect_robots_txt,
            settings=self.settings,
            url_builder=self.url_builder,
        )

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


def fetch_url(link, settings=None):
    u = url_builder(url=link, settings=settings)
    u.get_response()
    return u


async def fetch_all_urls(links, settings=None, url_builder=None, max_concurrency=10):
    num_pages = int(len(links) / max_concurrency)
    num_pages_mod = len(links) % max_concurrency

    if num_pages_mod != 0:
        num_pages += 1

    for num_page in range(num_pages):
        page_start = num_page * max_concurrency
        page_stop = page_start + max_concurrency

        tasks = []

        for link in links[page_start:page_stop]:
            tasks.append(asyncio.to_thread(fetch_url, link, settings, url_builder))

        result = await asyncio.gather(*tasks)
        return result
