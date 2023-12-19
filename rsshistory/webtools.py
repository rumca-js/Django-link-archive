"""
If you see contents of your own domain:
https://support.bunny.net/hc/en-us/articles/360017484759-The-CDN-URLs-are-returning-redirects-back-to-my-domain

Sometimes we see the CDN URLs return a 301 redirect back to your own website. Usually, when this happens, it's caused by a misconfiguration of your origin server and the origin URL of your pull zone. If the origin URL sends back a redirect, our servers will simply forward that to the user.

Disabling SSL validation will not check certificates, if expired.
"""

import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import urllib.robotparser

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

import html
import traceback
import requests
import re
import os

from datetime import datetime
from dateutil import parser

from bs4 import BeautifulSoup

from .models import PersistentInfo
from .apps import LinkDatabase


URL_TYPE_RSS = "rss"
URL_TYPE_CSS = "css"
URL_TYPE_JAVASCRIPT = "javascript"
URL_TYPE_HTML = "html"
URL_TYPE_UNKNOWN = "unknown"

"""
This is program is web scraper. If we turn verify, then we discard some of pages.
Encountered several major pages, which had SSL programs.

SSL is mostly important for interacting with pages. During web scraping it is not that useful.
"""
disable_warnings(InsecureRequestWarning)


class BasePage(object):
    """
    Should not contain any HTML/RSS content processing
    """

    # use headers from https://www.supermonitoring.com/blog/check-browser-http-headers/
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
    get_contents_function = None

    def __init__(self, url, contents=None):
        self.url = url

        if self.url.find("https") >= 0:
            self.protocol = "https"
        elif self.url.find("http") >= 0:
            self.protocol = "http"
        else:
            self.protocol = "https"

        self.contents = contents
        if self.contents:
            self.process_contents()

        # Flag to not retry same contents requests for things we already know are dead
        self.dead = False

        self.status_code = 0

        if BasePage.get_contents_function is None:
            self.get_contents_function = self.get_contents_internal

        if self.contents is None:
            from .configuration import Configuration

            config = Configuration.get_object()
            self.user_agent = config.config_entry.user_agent

    def process_contents(self):
        pass

    def is_valid(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return False

        if self.is_status_ok() == False:
            return False

        return True

    def try_decode(self, thebytes):
        try:
            return thebytes.decode("UTF-8", errors="replace")
        except Exception as e:
            pass

    def get_robots_txt_url(self):
        return self.get_domain() + "/robots.txt"

    def is_robots_txt(self):
        robots_file = self.get_robots_txt_url()
        p = BasePage(robots_file)
        if p.get_contents() != None:
            return True

    def get_robots_txt_obj(self):
        """
        https://developers.google.com/search/docs/crawling-indexing/robots/intro
        """
        self.rp = urllib.robotparser.RobotFileParser()
        domain = self.get_domain()
        self.rp.set_url(self.get_robots_txt_url())

        return self.rp

    def get_site_maps(self):
        """
        https://stackoverflow.com/questions/2978144/pythons-robotparser-ignoring-sitemaps
        robot parser does not work. We have to do it manually
        """
        result = set()

        p = HtmlPage(self.get_robots_txt_url())
        contents = p.get_contents()
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

    def is_status_ok(self):
        if self.status_code == 0:
            return False

        if self.status_code == 403:
            # Many pages return 403, but they are correct
            return True

        return self.status_code >= 200 and self.status_code < 300

    def get_contents(self):
        contents = self.get_contents_implementation()
        if not contents:
            if self.url.startswith("https://"):
                self.url = self.url.replace("https://", "http://")
                contents = self.get_contents_implementation()

        self.contents = contents
        return contents

    def get_contents_implementation(self):
        if self.contents:
            return self.contents

        if not self.user_agent or self.user_agent == "":
            return None

        if self.dead:
            return None

        if self.url == "http://" or self.url == "https://" or self.url == None:
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            PersistentInfo.error(
                "Page: Url is invalid{};Lines:{}".format(self.url, line_text)
            )

            return None

        hdr = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "ISO-8859-1,utf-8;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }

        try:
            # traceback.print_stack()

            r = self.get_contents_function(self.url, headers=hdr, timeout=10)
            self.status_code = r.status_code

            """
            The default assumed content encoding for text/html is ISO-8859-1 aka Latin-1 :( See RFC-2854. UTF-8 was too young to become the default, it was born in 1993, about the same time as HTML and HTTP.
            Use .content to access the byte stream, or .text to access the decoded Unicode stream.

            Override encoding by real educated guess as provided by chardet
            """
            r.encoding = r.apparent_encoding

            self.contents = r.text
            self.contents_bytes = r.content

            self.process_contents()

            return r.text

        except Exception as e:
            self.dead = True
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "Page: Error while reading page:{};Error:{}".format(self.url, str(e))
            )

    def get_contents_internal(self, url, headers, timeout):
        LinkDatabase.info("Page: Requesting page: {}".format(url))

        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """
        request_result = requests.get(url, headers=headers, timeout=timeout, verify=False)

        return request_result

    def get_full_url(self):
        if self.url.find("http") == -1:
            return "https://" + self.url
        return self.url

    def get_domain(self):
        if self.url.find("http") == -1:
            self.url = "https://" + self.url

        items = urlparse(self.url)
        if items.netloc is None or str(items.netloc) == "":
            return self.url
        return self.protocol + "://" + str(items.netloc)

    def get_domain_only(self):
        if self.url.find("http") == -1:
            self.url = "https://" + self.url

        items = urlparse(self.url)
        if items.netloc is None or str(items.netloc) == "":
            return self.url
        return str(items.netloc)

    def is_domain(self):
        url = self.get_full_url()
        if url == self.get_domain():
            return True

        return False

    def get_page_ext(self):
        url = self.get_clean_url()

        # domain level does not say anything if it is HTML page, or not
        if url == self.get_domain():
            return

        if url.endswith("/"):
            return

        sp = url.split(".")
        if len(sp) > 1:
            ext = sp[-1]
            if len(ext) < 5:
                return ext

        return

    def get_clean_url(self):
        url = self.url
        if url.find("?") >= 0:
            wh = url.find("?")
            return url[:wh]
        else:
            return url

    def get_url_full(domain, url):
        ready_url = ""
        if url.find("http") == 0:
            ready_url = url
        else:
            if url.startswith("//"):
                ready_url = "https:" + url
            elif url.startswith("/"):
                if not domain.endswith("/"):
                    domain = domain + "/"
                if url.startswith("/"):
                    url = url[1:]

                ready_url = domain + url
            else:
                if not domain.endswith("/"):
                    domain = domain + "/"
                ready_url = domain + url
        return ready_url


class DomainAwarePage(BasePage):
    def __init__(self, url, contents=None):
        super().__init__(url, contents)

    def is_mainstream(self):
        dom = self.get_domain_only()

        # wallet gardens which we will not accept

        mainstream = [
            "www.facebook",
            "www.rumble",
            "wikipedia.org",
            "twitter.com",
            "www.reddit.com",
            "stackoverflow.com",
            "www.quora.com",
        ]

        for item in mainstream:
            if dom.find(item) >= 0:
                return True

        if self.is_youtube():
            return True

        return False

    def is_youtube(self):
        dom = self.get_domain_only()
        if (
            dom.find("youtube.com") >= 0
            or dom.find("youtu.be") >= 0
            or dom.find("www.m.youtube") >= 0
        ):
            return True
        return False

    def is_analytics(self):
        if self.url.endswith("g.doubleclick.net"):
            return True
        if self.url.endswith("ad.doubleclick.net"):
            return True
        if self.url.endswith("doubleverify.com"):
            return True
        if self.url.endswith("adservice.google.com"):
            return True
        if self.url.endswith("amazon-adsystem.com"):
            return True
        if self.url.find("googlesyndication") >= 0:
            return True
        if self.url.endswith("www.googletagmanager.com"):
            return True
        if self.url.find("google-analytics") >= 0:
            return True
        if self.url.find("googletagservices") >= 0:
            return True
        if self.url.endswith("cdn.speedcurve.com"):
            return True
        if self.url.endswith("amazonaws.com"):
            return True
        if self.url.endswith("consent.cookiebot.com"):
            return True
        if self.url.endswith("cloudfront.net"):
            return True
        if self.url.endswith("prg.smartadserver.com"):
            return True
        if self.url.endswith("ads.us.e-planning.net"):
            return True
        if self.url.endswith("static.ads-twitter.com"):
            return True
        if self.url.endswith("analytics.twitter.com "):
            return True

    def is_link(self):
        return self.get_type_for_link() == URL_TYPE_HTML

    def get_type_for_link(self):
        the_type = self.get_type_by_ext()
        if the_type:
            return the_type

        ext = self.get_page_ext()
        if not ext:
            return URL_TYPE_HTML

        return URL_TYPE_UNKNOWN

    def is_html(self):
        return self.get_type() == URL_TYPE_HTML

    def is_rss(self):
        return self.get_type() == URL_TYPE_RSS

    def get_type(self):
        the_type = self.get_type_by_ext()
        if the_type:
            return the_type

        ext = self.get_page_ext()
        if not ext:
            return URL_TYPE_HTML

        ext = self.get_page_ext()
        if not ext:
            return self.get_type_by_checking_contents()

        if ext.lower() == "xml":
            return self.get_type_by_checking_contents()

        return URL_TYPE_UNKNOWN

    def get_type_by_ext(self):
        if self.is_analytics():
            return

        ext_mapping = {
            "css": URL_TYPE_CSS,
            "js": URL_TYPE_JAVASCRIPT,
            "html": URL_TYPE_HTML,
            "htm": URL_TYPE_HTML,
            "php": URL_TYPE_HTML,
            "aspx": URL_TYPE_HTML,
        }

        ext = self.get_page_ext()
        if ext:
            if ext in ext_mapping:
                return ext_mapping[ext]

        # if not found, we return none

    def get_type_by_checking_contents(self):
        if self.is_contents_html():
            return URL_TYPE_HTML
        if self.is_contents_rss():
            return URL_TYPE_RSS

    def is_contents_html(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            LinkDatabase.info("Could not obtain contents for {}".format(self.url))
            return

        if self.contents.find("DOCTYPE html") >= 0:
            return True
        if self.contents.find("<html") >= 0:
            return True
        if self.contents.find("<body") >= 0:
            return True

    def is_contents_rss(self):
        contents = self.get_contents()

        if not self.contents:
            LinkDatabase.info("Could not obtain contents for {}".format(self.url))
            return

        if (
            contents.find("<channel>") >= 0
            and contents.find("<title>") >= 0
            and contents.find("<item>") >= 0
        ):
            return True

        try:
            import feedparser

            feed = feedparser.parse(contents)
            if len(feed.entries) > 0:
                return True
            return False
        except Exception as e:
            return False


class ContentInterface(DomainAwarePage):
    def __init__(self, url, contents=None):
        super().__init__(url, contents)

    def get_title(self):
        raise NotImplementedError

    def get_description(self):
        raise NotImplementedError

    def get_language(self):
        raise NotImplementedError

    def get_thumbnail(self):
        raise NotImplementedError

    def get_author(self):
        raise NotImplementedError

    def get_album(self):
        raise NotImplementedError

    def get_tags(self):
        raise NotImplementedError

    def get_page_rating(self):
        raise NotImplementedError

    def get_properties(self):
        props = {}

        props["link"] = self.url
        props["title"] = self.get_title()
        props["description"] = self.get_description()
        props["author"] = self.get_author()
        props["album"] = self.get_album()
        props["thumbnail"] = self.get_thumbnail()
        props["language"] = self.get_language()
        props["page_rating"] = self.get_page_rating()
        props["tags"] = self.get_tags()

        return props


class RssPage(ContentInterface):
    """
    Handles RSS parsing.
    Do not use feedparser directly enywhere. We use BasicPage
    which allows to define timeouts.
    """

    def __init__(self, url, contents=None):
        super().__init__(url, contents)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None
        self.feed = None

    def parse(self):
        try:
            contents = self.get_contents()

            if contents is None:
                return None

            import feedparser

            self.feed = feedparser.parse(contents)
            return self.feed

        except Exception as e:
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "RssPage: when parsing:{};Error:{};{}".format(
                    self.url, str(e), error_text
                )
            )

    def parse_and_process(self):
        result = []
        try:
            if self.feed is None:
                self.feed = self.parse()

            if self.feed:
                result = self.process_feed()

        except Exception as e:
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "RssPage: when parsing:{};Error:{};{}".format(
                    self.url, str(e), error_text
                )
            )
            traceback.print_stack()
            traceback.print_exc()
        return result

    def process_feed(self):
        props = []

        for feed_entry in self.feed.entries:
            entry_props = self.get_feed_entry_map(feed_entry)
            if entry_props is not None:
                props.append(entry_props)

        return props

    def get_feed_entry_map(self, feed_entry):
        output_map = {}

        output_map["description"] = self.get_feed_description(feed_entry)
        output_map["thumbnail"] = self.get_feed_thumbnail(feed_entry)
        output_map["date_published"] = self.get_feed_date_published(feed_entry)
        output_map["source"] = self.url
        output_map["title"] = feed_entry.title
        output_map["language"] = self.get_language()
        output_map["link"] = feed_entry.link
        output_map["artist"] = self.get_author()
        output_map["album"] = ""
        output_map["bookmarked"] = False

        from .dateutils import DateUtils
        if output_map["date_published"] > DateUtils.get_datetime_now_utc():
            output_map["date_published"] = DateUtils.get_datetime_now_utc()

        if str(feed_entry.title).strip() == "" or feed_entry.title == "undefined":
            output_map["title"] = output_map["link"]

        return output_map

    def get_feed_description(self, feed_entry):
        if hasattr(feed_entry, "description"):
            return feed_entry.description
        else:
            return ""

    def get_feed_thumbnail(self, feed_entry):
        if hasattr(feed_entry, "media_thumbnail"):
            if len(feed_entry.media_thumbnail) > 0:
                thumb = feed_entry.media_thumbnail[0]
                if "url" in thumb:
                    return thumb["url"]
                else:
                    return str(thumb)
        else:
            return self.get_thumbnail()

        return None

    def get_feed_date_published(self, feed_entry):
        from .dateutils import DateUtils

        if hasattr(feed_entry, "published"):
            try:
                dt = parser.parse(feed_entry.published)

                return DateUtils.to_utc_date(dt)
            except Exception as e:
                PersistentInfo.error(
                    "Rss parser datetime invalid feed datetime:{}; Exc:{} {}\n{}".format(
                        feed_entry.published, str(e), ""
                    )
                )
                return DateUtils.get_datetime_now_utc()

        elif self.allow_adding_with_current_time:
            return DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            return self.default_entry_timestamp
        else:
            return DateUtils.get_datetime_now_utc()

    def get_title(self):
        if self.feed is None:
            self.parse()

        if "title" in self.feed.feed:
            return self.feed.feed.title

    def get_description(self):
        if self.feed is None:
            self.parse()

        if "subtitle" in self.feed.feed:
            return self.feed.feed.subtitle

    def get_language(self):
        if self.feed is None:
            self.parse()

        if "language" in self.feed.feed:
            return self.feed.feed.language

    def get_thumbnail(self):
        if self.feed is None:
            self.parse()

        image = None
        if "image" in self.feed.feed:
            if "href" in self.feed.feed.image:
                image = self.feed.feed.image["href"]
            elif "url" in self.feed.feed.image:
                image = self.feed.feed.image["url"]
            else:
                image = self.feed.feed.image

        if not image:
            if self.url.find("https://www.youtube.com/feeds/videos.xml") >= 0:
                image = self.get_thumbnail_manual_from_youtube()

        if image and image.find("https://") == -1:
            image = BasePage.get_url_full(self.get_domain(), image)

        return image

    def get_thumbnail_manual_from_youtube(self):
        if "link" in self.feed.feed:
            link = self.feed.feed.link
            p = HtmlPage(link)
            return p.get_thumbnail()

    def get_author(self):
        if self.feed is None:
            self.parse()

        if "author" in self.feed.feed:
            return self.feed.feed.author

    def get_album(self):
        return None

    def get_page_rating(self):
        rating = 0

        if self.get_title():
            rating += 5
        if self.get_description():
            rating += 5
        if self.get_language():
            rating += 1
        if self.get_thumbnail():
            rating += 1
        if self.get_author():
            rating += 1

        return rating

    def get_tags(self):
        return None


class ContentLinkParser(BasePage):
    """
    TODO filter also html from non html
    """

    def __init__(self, url, contents=None):
        super().__init__(url, contents)
        self.url = self.get_clean_url()

    def get_contents(self):
        return self.contents

    def get_links(self):
        links = set()

        links.update(self.get_links_https())
        links.update(self.get_links_href())

        if None in links:
            links.remove(None)
        if "" in links:
            links.remove("")
        if "http" in links:
            links.remove("http")
        if "https" in links:
            links.remove("https")
        if "http://" in links:
            links.remove("http://")
        if "https://" in links:
            links.remove("https://")

        result = set()
        for link in links:
            link = link.replace("http://", "https://")
            result.add(link)

        return links

    def get_links_https(self):
        cont = str(self.get_contents())

        allt = re.findall("(https?://[a-zA-Z0-9./\-_?&=]+)", cont)
        return set(allt)

    def get_links_href(self):
        url = self.url
        links = set()

        cont = str(self.get_contents())

        allt2 = re.findall('href="([a-zA-Z0-9./\-_]+)', cont)
        for item in allt2:
            if item.find("http") == 0:
                ready_url = item
            else:
                if item.startswith("//"):
                    ready_url = "https:" + item
                else:
                    if item.startswith("/"):
                        url = self.get_domain()

                    if not url.endswith("/"):
                        url = url + "/"
                    if item.startswith("/"):
                        item = item[1:]

                    ready_url = url + item

            links.add(ready_url)

        return links

    def filter_link_html(links):
        result = set()
        for link in links:
            p = DomainAwarePage(link)
            if p.is_link():
                result.add(link)

        return result

    def filter_link_in_domain(links, domain):
        result = set()

        for link in links:
            if link.find(domain) >= 0:
                result.add(link)

        return result

    def filter_link_in_url(links, url):
        result = set()

        for link in links:
            if link.find(url) >= 0:
                result.add(link)

        return result

    def filter_link_out_domain(links, domain):
        result = set()

        for link in links:
            if link.find(domain) < 0:
                result.add(link)

        return result

    def filter_link_out_url(links, url):
        result = set()

        for link in links:
            if link.find(url) < 0:
                result.add(link)

        return result

    def filter_domains(links):
        result = set()
        for link in links:
            p = BasePage(link)
            result.add(p.get_domain())

        return result


class HtmlPage(ContentInterface):
    def __init__(self, url, contents=None):
        super().__init__(url, contents)

    def process_contents(self):
        if self.contents:
            self.soup = BeautifulSoup(self.contents, "html.parser")

    def get_language(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return ""

        html = self.soup.find("html")
        if html and html.has_attr("lang"):
            return html["lang"]

        return ""

    def get_title_meta(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        title = None

        title_find = self.soup.find("title")
        if title_find:
            title = title_find.string

        return title

    def get_og_field(self, name):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        field = None

        field_find = self.soup.find("meta", property="og:{}".format(name))
        if field_find and field_find.has_attr("content"):
            field = field_find["content"]

        return field

    def get_title(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        title = None

        title = self.get_og_field("title")
        if not title:
            title = self.get_title_meta()

        if title:
            title = title.strip()

            # TODO hardcoded. Some pages provide such a dumb title with redirect
            if title.find("Just a moment...") >= 0:
                title = self.url

        if not title or title == "":
            title = self.url

        return title
        # title = html.unescape(title)

    def get_charset(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        charset = None

        allmeta = self.soup.findAll("meta")
        for meta in allmeta:
            if "charset" in meta.attrs:
                return meta.attrs["charset"]

    def get_description_meta(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        description = None

        description_find = self.soup.find("meta", attrs={"name": "description"})
        if description_find and description_find.has_attr("content"):
            description = description_find["content"]

        return description

    def get_author(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        author = None

        author_find = self.soup.find("meta", attrs={"name": "author"})
        if author_find and author_find.has_attr("content"):
            author = author_find["content"]

        return author

    def get_album(self):
        return None

    def get_thumbnail(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        image = self.get_og_field("image")
        if image and image.find("https://") == -1:
            image = BasePage.get_url_full(self.get_domain(), image)

        return image

    def get_tags(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        keywords = None

        keywords_find = self.soup.find("meta", attrs={"name": "keywords"})
        if keywords_find and keywords_find.has_attr("content"):
            keywords = keywords_find["content"]

        return keywords

    def get_description(self):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        description = None

        description = self.get_og_field("description")
        if not description:
            description = self.get_description_meta()

        if description:
            description = description.strip()

        return description

    def get_description_safe(self):
        desc = self.get_description()
        if not desc:
            return ""
        return desc

    def is_link_valid(self, address):
        return self.is_link_valid_domain(address)

    def is_link_valid_domain(self, address):
        if not address.startswith(self.get_domain()):
            return False
        return True

    def get_rss_url(self, full_check=False):
        urls = self.get_rss_urls()
        if urls and len(urls) > 0:
            return urls[0]

    def get_rss_urls(self, full_check=False):
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        rss_finds = self.soup.find_all("link", attrs={"type": "application/rss+xml"})

        rss_links = []
        for rss_find in rss_finds:
            if rss_find and rss_find.has_attr("href"):
                rss_links.append(rss_find["href"])

        rss_finds = self.soup.find_all(
            "link", attrs={"type": "application/rss+xml;charset=UTF-8"}
        )

        for rss_find in rss_finds:
            if rss_find and rss_find.has_attr("href"):
                rss_links.append(rss_find["href"])

        feed_url = self.url + "/feed"
        if full_check and feed_url not in rss_links:
            lucky_shot = self.url + "/feed"
            try:
                parser = RssPage(lucky_shot)
                feed = parser.parse()
                if len(feed.entries) > 0:
                    rss_links.append(lucky_shot)
            except Exception as e:
                LinkDatabase.info(
                    "WebTools exception during rss processing {}".format(str(e))
                )

        if len(rss_links) > 0:
            rss_urls = []
            for rss_url in rss_links:
                rss_url = BasePage.get_url_full(self.get_domain(), rss_url)
                rss_urls.append(rss_url)
            return rss_urls
        return []

    def get_links(self):
        p = ContentLinkParser(self.url, self.get_contents())
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return links

    def get_links_inner(self):
        p = ContentLinkParser(self.url, self.get_contents())
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return ContentLinkParser.filter_link_in_domain(links, self.get_domain())

    def get_links_outer(self):
        p = ContentLinkParser(self.url, self.get_contents())
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        in_domain = ContentLinkParser.filter_link_in_domain(
            p.get_links(), self.get_domain()
        )
        return links - in_domain

    def get_domains(self):
        p = ContentLinkParser(self.url, self.get_contents())
        links = p.get_links()
        links = ContentLinkParser.filter_domains(links)
        return links

    def get_domain_page(self):
        if self.url == self.get_domain():
            return self

        return Page(self.get_domain())

    def download_all(self):
        from .programwrappers.wget import Wget

        wget = Wget(self.url)
        wget.download_all()

    def get_properties(self):
        props = super().get_properties()

        props["meta_title"] = self.get_title_meta()
        props["meta_description"] = self.get_description_meta()
        props["og_title"] = self.get_og_field("title")
        props["og_description"] = self.get_og_field("description")
        props["og_image"] = self.get_og_field("image")
        # props["is_html"] = self.is_html()
        props["charset"] = self.get_charset()
        props["rss_urls"] = self.get_rss_urls()
        props["status_code"] = self.status_code

        if self.is_domain():
            if self.is_robots_txt():
                props["robots_txt_url"] = self.get_robots_txt_url()
                props["site_maps_urls"] = self.get_site_maps()

        props["links"] = self.get_links()
        props["links_inner"] = self.get_links_inner()
        props["links_outer"] = self.get_links_outer()
        props["contents"] = self.get_contents()
        if self.get_contents():
            props["contents_length"] = len(self.get_contents())

        return props

    def get_page_rating(self):
        rating = 0

        title_meta = self.get_title_meta()
        title_og = self.get_og_field("title")
        description_meta = self.get_description_meta()
        description_og = self.get_og_field("description")
        image_og = self.get_og_field("image")
        language = self.get_language()

        rating += self.get_page_rating_title(title_meta)
        rating += self.get_page_rating_title(title_og)
        rating += self.get_page_rating_description(description_meta)
        rating += self.get_page_rating_description(description_og)
        rating += self.get_page_rating_status_code(self.status_code)
        rating += self.get_page_rating_language(language)

        if self.get_author() != None:
            rating += 1
        if self.get_tags() != None:
            rating += 1

        if image_og:
            rating += 5

        return rating

    def get_page_rating_title(self, title):
        rating = 0
        if title is not None:
            if len(title) > 1000:
                rating += 5
            elif len(title.split(" ")) < 2:
                rating += 5
            elif len(title) < 4:
                rating += 2
            else:
                rating += 10

        return rating

    def get_page_rating_description(self, description):
        rating = 0
        if description is not None:
            rating += 5

        return rating

    def get_page_rating_language(self, language):
        rating = 0
        if language is not None:
            rating += 5
        if language.find("en") >= 0:
            rating += 1

        return rating

    def get_page_rating_status_code(self, status_code):
        rating = 0
        if status_code == 200:
            rating += 10
        elif status_code >= 200 and status_code <= 300:
            rating += 5
        elif status_code != 0:
            rating += 1

        return rating

    def is_valid(self):
        """
        This is a simple set of rules in which we reject the page.
        Some checks rely on the title.

        This is because some pages return valid HTTP return code, with a title informing about error.
        Therefore we use HTML title as means to find some most obvious errors.

        A user could have selected a title with these prohibited keywords, but I must admit this would not be wise
        to have "Site not found" string in the title.
        Better to reject such site either way.
        """
        if BasePage.is_valid(self) == False:
            LinkDatabase.info("Base page invalid indication")
            return False

        title = self.get_title()
        is_title_invalid = title and (
            title.find("Forbidden") >= 0
            or title.find("Access denied") >= 0
            or title.find("Site not found") >= 0
        )

        if is_title_invalid:
            LinkDatabase.info("Title is invalid {}".format(title))
            return False

        return True


class Url(object):
    def get(url, contents = None):
        """
        @returns Appropriate handler for the link
        """
        p = HtmlPage(url, contents)
        if p.is_html():
            return p

        if p.is_rss():
            return RssPage(url, p.get_contents())
