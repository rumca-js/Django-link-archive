import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import urllib.robotparser

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

        if self.contents:
            return True
        else:
            return False

    def try_decode(self, thebytes):
        try:
            return thebytes.decode("UTF-8", errors="replace")
        except Exception as e:
            pass

    def get_robots_txt(self):
        """
        https://developers.google.com/search/docs/crawling-indexing/robots/intro
        """
        self.rp = urllib.robotparser.RobotFileParser()
        domain = self.get_domain()
        self.rp.set_url("{}/robots.txt".format(domain))

        return self.rp

    def is_status_ok(self):
        if self.status_code == 0:
            return False

        print("Status code:{}".format(self.status_code))
        if self.status_code == 403:
            # Many pages return 403, but they are correct
            return True

        return self.status_code >= 200 and self.status_code < 300

    def get_contents_internal(self, url, headers, timeout):
        print("[{}] Page: Requesting page: {}".format(LinkDatabase.name, url))
        return requests.get(url, headers=headers, timeout=timeout)

    def get_contents(self):
        if self.contents:
            return self.contents

        if not self.user_agent or self.user_agent == "":
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
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "Page: Error while reading page:{};Error:{};{}".format(
                    self.url, str(e), error_text
                )
            )

    def get_domain(self):
        items = urlparse(self.url)
        if items.netloc is None or str(items.netloc) == "":
            return self.url
        return self.protocol + "://" + str(items.netloc)

    def get_domain_only(self):
        items = urlparse(self.url)
        if items.netloc is None or str(items.netloc) == "":
            return self.url
        return str(items.netloc)

    def is_html(self, check_contents=False):
        if self.is_analytics():
            return False

        ext = self.get_page_ext()
        if ext:
            if ext == "js" or ext == "css":
                return False

        if check_contents:
            if not self.contents:
                self.contents = self.get_contents()

            if not self.contents:
                print("Could not obtain contents for {}".format(self.url))
                return

            if self.contents.find("DOCTYPE html") >= 0:
                return True
            if self.contents.find("<html") >= 0:
                return True
            if self.contents.find("<body") >= 0:
                return True
        else:
            return True

    def is_rss(self):
        try:
            import feedparser

            feed = feedparser.parse(self.get_contents())
            if len(feed.entries) > 0:
                return True
            return False
        except Exception as e:
            return False

    def is_domain_level_url(self):
        if self.url.find("/", 9) >= 0:
            return False

        return True

    def get_page_ext(self):
        if self.is_domain_level_url():
            return ""
        else:
            url = self.get_clean_url()
            sp = url.split(".")
            if len(sp) > 1:
                ext = sp[-1]
                if len(ext) < 5:
                    return ext

        return ""

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
                ready_url = domain + url
        return ready_url

    def is_analytics(self):
        if self.url.find("g.doubleclick") >= 0:
            return True
        if self.url.find("doubleverify.com") >= 0:
            return True
        if self.url.find("adservice.google.com") >= 0:
            return True
        if self.url.find("amazon-adsystem.com") >= 0:
            return True
        if self.url.find("googlesyndication") >= 0:
            return True
        if self.url.find("google-analytics") >= 0:
            return True
        if self.url.find("googletagservices") >= 0:
            return True
        if self.url.find("cdn.speedcurve.com") >= 0:
            return True
        if self.url.find("amazonaws.com") >= 0:
            return True


class RssPage(BasePage):
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
        from .dateutils import DateUtils

        output_map = {}

        if hasattr(feed_entry, "description"):
            output_map["description"] = feed_entry.description
        else:
            output_map["description"] = ""

        if hasattr(feed_entry, "media_thumbnail"):
            if len(feed_entry.media_thumbnail) > 0:
                thumb = feed_entry.media_thumbnail[0]
                if "url" in thumb:
                    output_map["thumbnail"] = thumb["url"]
                else:
                    output_map["thumbnail"] = str(thumb)
        else:
            output_map["thumbnail"] = self.get_thumbnail()

        if "thumbnail" not in output_map:
            output_map["thumbnail"] = None

        if hasattr(feed_entry, "published"):
            try:
                dt = parser.parse(feed_entry.published)
                output_map["date_published"] = dt
            except Exception as e:
                PersistentInfo.error(
                    "Rss parser datetime invalid feed datetime:{}; Exc:{} {}\n{}".format(
                        feed_entry.published, str(e), ""
                    )
                )
                output_map["date_published"] = DateUtils.get_datetime_now_utc()

        elif self.allow_adding_with_current_time:
            output_map["date_published"] = DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            output_map["date_published"] = self.default_entry_timestamp
        else:
            output_map["date_published"] = DateUtils.get_datetime_now_utc()

        output_map["source"] = self.url
        output_map["title"] = feed_entry.title
        language = self.get_language()
        if language:
            output_map["language"] = language
        output_map["link"] = feed_entry.link
        author = self.get_author()
        if author:
            output_map["artist"] = author
        output_map["album"] = ""
        output_map["bookmarked"] = False

        if str(feed_entry.title).strip() == "" or feed_entry.title == "undefined":
            output_map["title"] = output_map["link"]

        if output_map["date_published"]:
            output_map["date_published"] = DateUtils.to_utc_date(
                output_map["date_published"]
            )

            if output_map["date_published"] > DateUtils.get_datetime_now_utc():
                output_map["date_published"] = DateUtils.get_datetime_now_utc()

        return output_map

    def get_title(self):
        if self.feed is None:
            self.parse()

        if "title" in self.feed.feed:
            return self.feed.feed.title

    def get_subtitle(self):
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

        if "image" in self.feed.feed:
            if "href" in self.feed.feed.image:
                return self.feed.feed.image["href"]
            elif "url" in self.feed.feed.image:
                return self.feed.feed.image["url"]
            else:
                return self.feed.feed.image

    def get_author(self):
        if self.feed is None:
            self.parse()

        if "author" in self.feed:
            return self.feed.feed.author


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
            p = BasePage(link)
            if p.is_html():
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


class HtmlPage(BasePage):
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
        if not self.contents:
            self.contents = self.get_contents()

        if not self.contents:
            return None

        rss_url = None

        rss_find = self.soup.find("link", attrs={"type": "application/rss+xml"})

        if rss_find and rss_find.has_attr("href"):
            rss_url = rss_find["href"]

        rss_find = self.soup.find(
            "link", attrs={"type": "application/rss+xml;charset=UTF-8"}
        )
        if rss_find and rss_find.has_attr("href"):
            rss_url = rss_find["href"]

        if rss_url:
            rss_url = BasePage.get_url_full(self.get_domain(), rss_url)
            # try:
            #    parser = RssPage(rss_url)
            #    feed = parser.parse()
            #
            #    print("RSS: {}".format(rss_url))
            #    print(len(feed.entries))
            #
            #    if len(feed.entries) > 0:
            #        return rss_url
            # except Exception as e:
            #    print("Exception {}".format(str(e)))
            return rss_url

        if not rss_url and full_check:
            lucky_shot = self.url + "/feed"
            try:
                parser = RssPage(lucky_shot)
                feed = parser.parse()
                if len(feed.entries) > 0:
                    rss_url = lucky_shot
            except Exception as e:
                print("Exception {}".format(str(e)))

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

    def download_all(self):
        from .programwrappers.wget import Wget

        wget = Wget(self.url)
        wget.download_all()

    def get_properties_map(self):
        props = {}

        props["link"] = self.url
        props["title"] = self.get_title()
        props["description"] = self.get_description()
        props["meta:title"] = self.get_title_meta()
        props["meta:description"] = self.get_description_meta()
        props["og:title"] = self.get_og_field("title")
        props["og:description"] = self.get_og_field("description")
        props["og:image"] = self.get_og_field("image")
        props["is_html"] = self.is_html()
        props["charset"] = self.get_charset()
        props["language"] = self.get_language()
        props["rss_url"] = self.get_rss_url()
        props["page_rating"] = self.get_page_rating()
        props["status_code"] = self.status_code
        props["links"] = self.get_links()
        props["links_inner"] = self.get_links_inner()
        props["links_outer"] = self.get_links_outer()
        props["contents"] = self.get_contents()
        return props

    def get_properties(self):
        props = []

        map_props = self.get_properties_map()
        for key in map_props:
            props.append((key, map_props[key]))

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
        if BasePage.is_valid(self) == False:
            return False

        title = self.get_title()
        is_title_invalid = title and (
            title.find("Forbidden") >= 0 or title.find("Access denied") >= 0
        )

        if self.is_status_ok() == False or is_title_invalid:
            return False
        return True
