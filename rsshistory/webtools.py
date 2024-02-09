"""
#1

This is program is web scraper. If we turn verify, then we discard some of pages.
Encountered several major pages, which had SSL programs.

SSL is mostly important for interacting with pages. During web scraping it is not that useful.

#2
If SSL verification is disabled you can see contents of your own domain:
https://support.bunny.net/hc/en-us/articles/360017484759-The-CDN-URLs-are-returning-redirects-back-to-my-domain

Sometimes we see the CDN URLs return a 301 redirect back to your own website. Usually, when this happens, it's caused by a misconfiguration of your origin server and the origin URL of your pull zone. If the origin URL sends back a redirect, our servers will simply forward that to the user.

Disabling SSL validation will not check certificates, if expired.
"""

import urllib.request, urllib.error, urllib.parse
from urllib.parse import urlparse
import urllib.robotparser

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from bs4 import BeautifulSoup

import html
import traceback
import requests
import re
import json

from datetime import datetime
from dateutil import parser

from .models import PersistentInfo
from .apps import LinkDatabase

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException
except Exception as E:
    print("Cannot include selenium")


URL_TYPE_RSS = "rss"
URL_TYPE_CSS = "css"
URL_TYPE_JAVASCRIPT = "javascript"
URL_TYPE_HTML = "html"
URL_TYPE_FONT = "font"
URL_TYPE_UNKNOWN = "unknown"


def lazy_load_content(func):
    """
    Lazy load for functions.
    We do not want page contents during construction.
    We want it only when necessary.
    """

    def wrapper(self, *args, **kwargs):
        if not self.contents:
            self.contents = self.get_contents()
        return func(self, *args, **kwargs)

    return wrapper


class SeleniumResponseObject(object):
    def __init__(self, url, contents):
        self.status_code = 200
        self.apparent_encoding = "utf-8"
        self.encoding = "utf-8"

        self.content = contents
        self.text = contents

        self.headers = {}


class PageOptions(object):
    def __init__(self):
        self.use_selenium_full = False
        self.use_selenium_headless = False
        self.ssl_verify = False
        self.fast_parsing = True
        self.custom_user_agent = ""

    def is_not_selenium(self):
        return not self.is_selenium()

    def is_selenium(self):
        return self.use_selenium_full or self.use_selenium_headless

    def __str__(self):
        return "Full:{} Headless:{} SSL verify:{}".format(
            self.use_selenium_full, self.use_selenium_headless, self.ssl_verify
        )


class BasePage(object):
    """
    Should not contain any HTML/RSS content processing
    """

    # use headers from https://www.supermonitoring.com/blog/check-browser-http-headers/
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
    get_contents_function = None
    ssl_verify = True

    def __init__(self, url, contents=None, options=None, page_obj=None):
        """
        @param url URL
        @param contents URL page contents
        @param use_selenium decides if selenium is used
        @param page_obj All settings are used from page object, with page contents
        """
        if page_obj:
            self.url = page_obj.url
            self.contents = page_obj.contents
            self.options = page_obj.options
            self.status_code = page_obj.status_code
            self.dead = page_obj.dead
            self.response_headers = page_obj.response_headers
            self.robots_contents = page_obj.robots_contents
        else:
            self.url = url
            self.options = options
            self.response_headers = {}
            self.robots_contents = None

            # Flag to not retry same contents requests for things we already know are dead
            self.dead = False

        if self.url.find("https") >= 0:
            self.protocol = "https"
        elif self.url.find("http") >= 0:
            self.protocol = "http"
        else:
            self.protocol = "https"

        self.contents = contents
        if self.contents:
            self.process_contents()
            self.status_code = 200
        else:
            self.status_code = 0

        if not self.options:
            self.options = PageOptions()

        if BasePage.get_contents_function is None:
            self.get_contents_function = self.get_contents_internal

    def disable_ssl_warnings():
        BasePage.ssl_verify = False
        disable_warnings(InsecureRequestWarning)

    def process_contents(self):
        pass

    @lazy_load_content
    def is_valid(self):
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

    def get_robots_txt_contents(self):
        if self.robots_contents:
            return self.robots_contents

        robots_url = self.get_robots_txt_url()
        p = BasePage(robots_url)
        self.robots_contents = p.get_contents()

        return self.robots_contents

    def is_robots_txt(self):
        return self.get_robots_txt_contents()

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

    def is_status_ok(self):
        if self.status_code == 0:
            return False

        if self.status_code == 403:
            # Many pages return 403, but they are correct
            return True

        return self.status_code >= 200 and self.status_code < 300

    def get_contents(self):
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
            r = self.get_contents_function(self.url, headers=hdr, timeout=10)

            self.status_code = r.status_code
            self.response_headers = r.headers

            """
            The default assumed content encoding for text/html is ISO-8859-1 aka Latin-1 :( See RFC-2854. UTF-8 was too young to become the default, it was born in 1993, about the same time as HTML and HTTP.
            Use .content to access the byte stream, or .text to access the decoded Unicode stream.

            Override encoding by real educated guess as provided by chardet
            """
            r.encoding = r.apparent_encoding

            self.contents = r.text

            self.process_contents()

            return r.text

        except Exception as e:
            LinkDatabase.info(str(e))

            self.dead = True
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "Page: Error while reading page:{};Error:{}\n{}".format(
                    self.url, str(e), error_text
                )
            )

    def get_contents_internal(self, url, headers, timeout):
        LinkDatabase.info(
            "Page: Requesting page: {} options:{}".format(url, self.options)
        )

        if self.options.is_not_selenium():
            return self.get_contents_via_requests(self.url, headers=headers, timeout=10)
        elif self.options.use_selenium_full:
            return self.get_contents_via_selenium_chrome_full(
                self.url, headers=headers, timeout=10
            )
        elif self.options.use_selenium_headless:
            return self.get_contents_via_selenium_chrome_headless(
                self.url, headers=headers, timeout=10
            )
        else:
            raise NotImplementedError("Could not identify method of page capture")

    def get_contents_via_requests(self, url, headers, timeout):
        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """

        # traceback.print_stack()

        request_result = requests.get(
            url, headers=headers, timeout=timeout, verify=BasePage.ssl_verify
        )

        return request_result

    def get_contents_via_selenium_chrome_headless(self, url, headers, timeout):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        driver = webdriver.Chrome(service=service, options=options)

        # add 10 seconds for start of browser, etc.
        selenium_timeout = timeout + 10

        driver.set_page_load_timeout(selenium_timeout)

        try:
            driver.get(url)
        except TimeoutException:
            PersistentInfo.error(
                "Timeout when reading page. {}".format(selenium_timeout)
            )

        html_content = driver.page_source

        driver.quit()

        return SeleniumResponseObject(url, html_content)

    def get_contents_via_selenium_chrome_full(self, url, headers, timeout):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
        """
        import os

        os.environ["DISPLAY"] = ":10.0"

        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(service=service, options=options)

        # add 10 seconds for start of browser, etc.
        selenium_timeout = timeout + 20

        driver.set_page_load_timeout(selenium_timeout)

        try:
            driver.get(url)
        except TimeoutException:
            PersistentInfo.error(
                "Timeout when reading page. {}".format(selenium_timeout)
            )

        page_source = driver.page_source

        ## Parse the HTML with BeautifulSoup
        # soup = BeautifulSoup(page_source, 'html.parser')

        ## Extract the RSS content from the HTML body
        # rss_content = soup.find('body').get_text()

        driver.quit()

        return SeleniumResponseObject(url, page_source)

    def get_contents_via_selenium_chrome_undetected(self, url, headers, timeout):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        This does not work on raspberry pi
        """
        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        driver = uc.Chrome(options=options)

        # add 10 seconds for start of browser, etc.
        selenium_timeout = timeout + 10

        driver.set_page_load_timeout(selenium_timeout)

        try:
            driver.get(url)
            time.sleep(5)
        except TimeoutException:
            PersistentInfo.error(
                "Timeout when reading page. {}".format(selenium_timeout)
            )

        html_content = driver.page_source

        driver.quit()

        return SeleniumResponseObject(url, html_content)

    def is_redirect(self):
        return self.status_code > 300 and self.status_code < 310

    def get_redirect_url(self):
        if self.is_redirect() and "Location" in self.response_headers.headers:
            return self.response_headers.headers["Location"]

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
        """
        @return extension, or none
        """
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
        """
        TODO change function name
        formats:
        href="images/facebook.png"
        href="/images/facebook.png"
        href="//images/facebook.png"
        href="https://images/facebook.png"
        """
        ready_url = ""
        if url.find("http") == 0:
            ready_url = url
        else:
            if url.startswith("//"):
                ready_url = "https:" + url
            elif url.startswith("/"):
                domain = BasePage(domain).get_domain()
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
    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)

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
            "www.instagram.com",
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
            dom == "youtube.com"
            or dom == "youtu.be"
            or dom == "www.m.youtube.com"
            or dom == "www.youtube.com"
        ):
            return True
        return False

    def is_analytics(self):
        url = self.get_domain_only()

        if url.find("g.doubleclick.net") >= 0:
            return True
        if url.find("ad.doubleclick.net") >= 0:
            return True
        if url.find("doubleverify.com") >= 0:
            return True
        if url.find("adservice.google.com") >= 0:
            return True
        if url.find("amazon-adsystem.com") >= 0:
            return True
        if url.find("googlesyndication") >= 0:
            return True
        if url.find("www.googletagmanager.com") >= 0:
            return True
        if url.find("google-analytics") >= 0:
            return True
        if url.find("googletagservices") >= 0:
            return True
        if url.find("cdn.speedcurve.com") >= 0:
            return True
        if url.find("amazonaws.com") >= 0:
            return True
        if url.find("consent.cookiebot.com") >= 0:
            return True
        if url.find("cloudfront.net") >= 0:
            return True
        if url.find("prg.smartadserver.com") >= 0:
            return True
        if url.find("ads.us.e-planning.net") >= 0:
            return True
        if url.find("static.ads-twitter.com") >= 0:
            return True
        if url.find("analytics.twitter.com") >= 0:
            return True
        if url.find("static.cloudflareinsights.com") >= 0:
            return True

    def is_link_service(self):
        url = self.get_domain_only()

        if url.find("lmg.gg") >= 0:
            return True
        if url.find("geni.us") >= 0:
            return True
        if url.find("tinyurl.com") >= 0:
            return True
        if url.find("bit.ly") >= 0:
            return True
        if url.find("amzn.to") >= 0:
            return True

        return False

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

    def is_html(self, fast_check=True):
        return self.get_type(fast_check) == URL_TYPE_HTML

    def is_rss(self, fast_check=True):
        return self.get_type(fast_check) == URL_TYPE_RSS

    def get_type(self, fast_check=True):
        the_type = self.get_type_by_ext()
        if the_type:
            return the_type

        ext = self.get_page_ext()
        if ext:
            if ext.lower() == "xml":
                return self.get_type_by_checking_contents()

            if ext.lower() == "rss":
                return self.get_type_by_checking_contents()

            if ext.lower() == "aspx":
                return self.get_type_by_checking_contents()

        if fast_check:
            ext = self.get_page_ext()
            if not ext:
                return URL_TYPE_HTML
        else:
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
            "woff2": URL_TYPE_FONT,
            "tff": URL_TYPE_FONT,
            # "php": URL_TYPE_HTML,    seen in the wild, where dynamic pages were used to generate RSS :(
            # "aspx": URL_TYPE_HTML,
        }

        ext = self.get_page_ext()
        if ext:
            if ext in ext_mapping:
                return ext_mapping[ext]

        # if not found, we return none

    def get_type_by_checking_contents(self):
        if self.is_contents_rss():
            return URL_TYPE_RSS
        if self.is_contents_html():
            return URL_TYPE_HTML

    @lazy_load_content
    def is_contents_html(self):
        """
        We want the checks to be simple yet effective. Check some tokens.

        There can be RSS sources in HTML, HTML inside RSS. Beware
        """
        if not self.contents:
            LinkDatabase.info("Could not obtain contents for {}".format(self.url))
            return

        html_tags = self.get_position_of_html_tags()
        rss_tags = self.get_position_of_rss_tags()

        if html_tags >= 0 and rss_tags >= 0:
            return html_tags < rss_tags
        if html_tags >= 0:
            return True

    @lazy_load_content
    def is_contents_rss(self):
        """
        We want the checks to be simple yet effective. Check some tokens.

        There can be RSS sources in HTML, HTML inside RSS. Beware
        """
        if not self.contents:
            LinkDatabase.info("Could not obtain contents for {}".format(self.url))
            return

        html_tags = self.get_position_of_html_tags()
        rss_tags = self.get_position_of_rss_tags()

        if html_tags >= 0 and rss_tags >= 0:
            return rss_tags < html_tags
        if rss_tags >= 0:
            return True

        """
        If we want to have full blown parsing. Not worth it.
        """
        try:
            import feedparser

            feed = feedparser.parse(self.contents)
            if len(feed.entries) > 0:
                return True
            return False
        except Exception as e:
            return False

    @lazy_load_content
    def get_position_of_html_tags(self):
        if not self.contents:
            return -1

        lower = self.contents.lower()
        if lower.find("<html") >= 0 and lower.find("<body") >= 0:
            return lower.find("<html")

        return -1

    @lazy_load_content
    def get_position_of_rss_tags(self):
        if not self.contents:
            return -1

        lower = self.contents.lower()
        if lower.find("<rss") >= 0 and lower.find("<channel") >= 0:
            return lower.find("<rss")

        return -1


class ContentInterface(DomainAwarePage):
    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)

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
        """
        Should be in range 0 - 100 (percentage).

        Allows us to extend properties, and not break existing page ratings.
        """
        raise NotImplementedError

    def get_date_published(self):
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
        props["date_published"] = self.get_date_published()
        props["tags"] = self.get_tags()

        return props

    def is_cloudflare_protected(self):
        contents = self.get_contents()

        if (
            contents
            and contents.find("https://static.cloudflareinsights.com/beacon.min.js/")
            >= 0
        ):
            return True

        return False

    def guess_date(self):
        """
        This is ugly, but dateutil.parser does not work. May generate exceptions.
        Ugly is better than not working.

        Supported formats:
         - Jan. 15, 2024
         - Jan 15, 2024
         - January 15, 2024
         - 15 January 2024 14:48 UTC
        """
        from .dateutils import DateUtils

        content = self.get_contents()
        if not content:
            return

        # searching will be case insensitive
        content = content.lower()

        # Get the current year
        current_year = int(datetime.now().year)

        # Define regular expressions
        current_year_pattern = re.compile(rf"\b{current_year}\b")
        four_digit_number_pattern = re.compile(r"\b\d{4}\b")

        # Attempt to find the current year in the string
        match_current_year = current_year_pattern.search(content)

        year = None
        scope = None

        if match_current_year:
            year = int(current_year)
            # Limit the scope to a specific portion before and after year
            scope = content[
                max(0, match_current_year.start() - 15) : match_current_year.start()
                + 20
            ]
        else:
            match_four_digit_number = four_digit_number_pattern.search(content)
            if match_four_digit_number:
                year = int(match_four_digit_number.group(0))
                # Limit the scope to a specific portion before and after year
                scope = content[
                    max(
                        0, match_four_digit_number.start() - 15
                    ) : match_four_digit_number.start()
                    + 20
                ]

        if scope:
            return self.guess_by_scope(scope, year)

    def guess_by_scope(self, scope, year):
        from .dateutils import DateUtils

        date_pattern_iso = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")

        month_re = "(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?"

        # 2024 jan 23
        date_pattern_us = re.compile(
            r"(\d{4})\s*{}\s*(\d{1,2})".replace("{}", month_re)
        )
        # jan 23 2024
        date_pattern_us2 = re.compile(
            r"{}\s*(\d{1,2})\s*(\d{4})".replace("{}", month_re)
        )
        # 23 jan 2024
        date_pattern_ue = re.compile(
            r"(\d{1,2})\s*{}\s*(\d{4})".replace("{}", month_re)
        )

        # only Jan 23, without year next by
        month_date_pattern = re.compile(r"\b{}\s*(\d+)\b".replace("{}", month_re))

        date_pattern_iso_match = date_pattern_iso.search(scope)
        date_pattern_us_match = date_pattern_us.search(scope)
        date_pattern_us2_match = date_pattern_us2.search(scope)
        date_pattern_ue_match = date_pattern_ue.search(scope)

        month_date_pattern_match = month_date_pattern.search(scope)

        date_object = None

        if date_pattern_iso_match:
            year, month, day = date_pattern_iso_match.groups()
            date_object = self.format_date(year, month, day)

        elif date_pattern_us_match:
            year, month, day = date_pattern_us_match.groups()
            date_object = self.format_date(year, month, day)

        elif date_pattern_us2_match:
            month, day, year = date_pattern_us2_match.groups()
            date_object = self.format_date(year, month, day)

        elif date_pattern_ue_match:
            day, month, year = date_pattern_ue_match.groups()
            date_object = self.format_date(year, month, day)

        # If a month and day are found, construct a datetime object with year, month, and day
        elif month_date_pattern_match:
            month, day = month_date_pattern_match.groups()
            date_object = self.format_date(year, month, day)

        elif year:
            current_year = int(datetime.now().year)

            if year >= current_year or year < 1900:
                date_object = datetime.now()
            else:
                # If only the year is found, construct a datetime object with year
                date_object = datetime(year, 1, 1)

        # For other scenario to not provide any value

        if date_object:
            date_object = DateUtils.to_utc_date(date_object)

        return date_object

    def format_date(self, year, month, day):
        from time import strptime

        month_number = None

        try:
            month_number = int(month)
            month_number = month
        except Exception as E:
            LinkDatabase.info("Error:{}".format(str(E)))

        if not month_number:
            try:
                month_number = strptime(month, "%b").tm_mon
                month_number = str(month_number)
            except Exception as E:
                LinkDatabase.info("Error:{}".format(str(E)))

        if not month_number:
            try:
                month_number = strptime(month, "%B").tm_mon
                month_number = str(month_number)
            except Exception as E:
                LinkDatabase.info("Error:{}".format(str(E)))

        if month_number is None:
            LinkDatabase.error(
                "Guessing date error: URL:{};\nYear:{};\nMonth:{}\nDay:{}".format(
                    self.url, year, month, day
                )
            )
            return

        try:
            date_object = datetime.strptime(
                f"{year}-{month_number.zfill(2)}-{day.zfill(2)}", "%Y-%m-%d"
            )

            return date_object
        except Exception as E:
            LinkDatabase.error(
                "Guessing date error: URL:{};\nYear:{};\nMonth:{}\nDay:{}".format(
                    self.url, year, month, day
                )
            )


class DefaultContentPage(ContentInterface):
    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)

    def get_title(self):
        return self.url

    def get_description(self):
        return None

    def get_language(self):
        return None

    def get_thumbnail(self):
        return None

    def get_author(self):
        return None

    def get_album(self):
        return None

    def get_tags(self):
        return None

    def get_date_published(self):
        return None

    def get_page_rating(self):
        page_rating = 0

        if self.get_title() is not None and str(self.get_title()) != "":
            page_rating += 10

        if self.get_description() is not None and str(self.get_description()) != "":
            page_rating += 5

        if self.get_language() is not None and str(self.get_language()) != "":
            page_rating += 1

        if self.get_thumbnail() is not None and str(self.get_thumbnail()) != "":
            page_rating += 1

        if (
            self.get_date_published() is not None
            and str(self.get_date_published()) != ""
        ):
            page_rating += 1

        max_page_rating = 10 + 5 + 1 + 1 + 1

        page_rating = (page_rating * 100) / max_page_rating

        return int(page_rating)


class JsonPage(ContentInterface):
    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)

        self.json_obj = None
        try:
            contents = self.get_contents()
            self.json_obj = json.loads(contents)
        except Exception as e:
            LinkDatabase.error("Invalid json:{}".format(contents))

    def is_json(self):
        if self.json_obj:
            return True

    def get_title(self):
        if self.json_obj and "title" in self.json_obj:
            return self.json_obj["title"]

    def get_description(self):
        if self.json_obj and "description" in self.json_obj:
            return self.json_obj["description"]

    def get_language(self):
        if self.json_obj and "language" in self.json_obj:
            return self.json_obj["language"]

    def get_thumbnail(self):
        if self.json_obj and "thumbnail" in self.json_obj:
            return self.json_obj["thumbnail"]

    def get_author(self):
        if self.json_obj and "author" in self.json_obj:
            return self.json_obj["author"]

    def get_album(self):
        if self.json_obj and "album" in self.json_obj:
            return self.json_obj["album"]

    def get_tags(self):
        if self.json_obj and "tags" in self.json_obj:
            return self.json_obj["tags"]

    def get_date_published(self):
        if self.json_obj and "date_published" in self.json_obj:
            return self.json_obj["date_published"]

    def get_page_rating(self):
        return 0


class RssPage(ContentInterface):
    """
    Handles RSS parsing.
    Do not use feedparser directly enywhere. We use BasicPage
    which allows to define timeouts.
    """

    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)
        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None
        self.feed = None

    @lazy_load_content
    def parse(self):
        try:
            contents = self.contents

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

    def get_container_elements(self):
        try:
            if self.feed is None:
                self.feed = self.parse()

            if self.feed:
                for item in self.get_container_elements_maps():
                    yield item

        except Exception as e:
            error_text = traceback.format_exc()

            PersistentInfo.error(
                "RssPage: when parsing:{};Error:{};{}".format(
                    self.url, str(e), error_text
                )
            )
            traceback.print_stack()
            traceback.print_exc()

    def get_container_elements_maps(self):
        for feed_entry in self.feed.entries:
            entry_props = self.get_feed_entry_map(feed_entry)
            if entry_props is not None:
                yield entry_props

    def get_feed_entry_map(self, feed_entry):
        output_map = {}

        if "link" not in feed_entry:
            return output_map

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
        output_map["feed_entry"] = feed_entry

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
        if hasattr(feed_entry, "media_content"):
            if len(feed_entry.media_content) > 0:
                thumb = feed_entry.media_content[0]
                if "url" in thumb:
                    return thumb["url"]
                else:
                    return str(thumb)

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

        if "description" in self.feed.feed:
            return self.feed.feed.description

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
                try:
                    image = str(self.feed.feed.image["href"])
                except Exception as E:
                    LinkDatabase.error(str(E))

            elif "url" in self.feed.feed.image:
                try:
                    image = str(self.feed.feed.image["url"])
                except Exception as E:
                    LinkDatabase.error(str(E))
            else:
                # cannot display self.feed.feed here.
                # it complains et_thumbnail TypeError: 'DeferredAttribute' object is not callable
                PersistentInfo.create(
                    "Unsupported image type for feed. {}".format(
                        str(self.feed.feed.image)
                    )
                )

        if not image:
            if self.url.find("https://www.youtube.com/feeds/videos.xml") >= 0:
                image = self.get_thumbnail_manual_from_youtube()

        if image and image.find("https://") == -1:
            image = BasePage.get_url_full(self.url, image)

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

    def get_date_published(self):
        if self.feed is None:
            self.parse()

        if "published" in self.feed.feed:
            return self.feed.feed.published

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

        rating = rating * 100 / self.get_max_page_rating()

        return int(rating)

    def get_max_page_rating(self):
        return 5 + 5 + 1 + 1 + 1

    def get_tags(self):
        return None

    def get_properties(self):
        props = super().get_properties()
        props["contents"] = self.get_contents()
        return props

    @lazy_load_content
    def is_valid(self):
        if super().is_valid() == False:
            return False

        if not self.is_contents_rss():
            return False

        return True


class ContentLinkParser(DomainAwarePage):
    """
    TODO filter also html from non html
    """

    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)
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
        # links cannot end with "."
        allt = [link.rstrip(".") for link in allt]
        return set(allt)

    def get_links_href(self):
        url = self.url
        links = set()

        cont = str(self.get_contents())

        allt = re.findall('href="([a-zA-Z0-9./\-_]+)', cont)
        allt = [link.rstrip(".") for link in allt]

        for item in allt:
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
    """
    Since links can be passed in various ways and formats, all links need to be "normalized" before
    returning.

    formats:
    href="images/facebook.png"
    href="/images/facebook.png"
    href="//images/facebook.png"
    href="https://images/facebook.png"
    """

    def __init__(self, url, contents=None, options=None, page_obj=None):
        super().__init__(url, contents=contents, options=options, page_obj=page_obj)

    def process_contents(self):
        if self.contents:
            self.soup = BeautifulSoup(self.contents, "html.parser")

    @lazy_load_content
    def get_head_field(self, field):
        if not self.contents:
            return None

        found_element = self.soup.find(field)
        if found_element:
            value = found_element.string
            if value != "":
                return value

    @lazy_load_content
    def get_meta_custom_field(self, field_type, field):
        if not self.contents:
            return None

        find_element = self.soup.find("meta", attrs={field_type: field})
        if find_element and find_element.has_attr("content"):
            return find_element["content"]

    @lazy_load_content
    def get_meta_field(self, field):
        if not self.contents:
            return None

        return self.get_meta_custom_field("name", field)

    @lazy_load_content
    def get_property_field(self, name):
        if not self.contents:
            return None

        field_find = self.soup.find("meta", property="{}".format(name))
        if field_find and field_find.has_attr("content"):
            return field_find["content"]

    @lazy_load_content
    def get_og_field(self, name):
        if not self.contents:
            return None

        return self.get_property_field("og:{}".format(name))

    @lazy_load_content
    def get_title(self):
        if not self.contents:
            return None

        title = self.get_og_field("title")
        if not title:
            title = self.get_title_meta()
            if not title:
                title = self.get_title_head()

        if title:
            title = title.strip()

            # TODO hardcoded. Some pages provide such a dumb title with redirect
            if title.find("Just a moment...") >= 0:
                title = self.url

        return title
        # title = html.unescape(title)

    @lazy_load_content
    def get_date_published(self):
        """
        There could be multiple places to read published time.
        We try every possible thing.
        """

        # used by mainstream media. Examples?
        date_str = self.get_property_field("article:published_time")
        if date_str:
            return self.date_str_to_date(date_str)

        # used by spotify
        date_str = self.get_meta_field("music:release_date")
        if date_str:
            return self.date_str_to_date(date_str)

        # used by youtube
        date_str = self.get_meta_custom_field("itemprop", "datePublished")
        if date_str:
            return self.date_str_to_date(date_str)

    def date_str_to_date(self, date_str):
        from .dateutils import DateUtils

        if date_str:
            try:
                parsed_date = parser.parse(date_str)
                return DateUtils.to_utc_date(parsed_date)
            except Exception as E:
                PersistentInfo.error(
                    "Could not parse music:release_date {} Exc:{}".format(
                        date_str, str(E)
                    )
                )

    @lazy_load_content
    def get_title_head(self):
        if not self.contents:
            return None

        return self.get_head_field("title")

    @lazy_load_content
    def get_title_meta(self):
        if not self.contents:
            return None

        return self.get_meta_field("title")

    @lazy_load_content
    def get_description(self):
        if not self.contents:
            return None

        description = self.get_og_field("description")
        if not description:
            description = self.get_description_meta()
            if not description:
                description = self.get_description_head()

        if description:
            description = description.strip()

        return description

    def get_description_safe(self):
        desc = self.get_description()
        if not desc:
            return ""
        return desc

    @lazy_load_content
    def get_description_head(self):
        if not self.contents:
            return None

        return self.get_head_field("description")

    @lazy_load_content
    def get_description_meta(self):
        if not self.contents:
            return None

        return self.get_meta_field("description")

    @lazy_load_content
    def get_thumbnail(self):
        if not self.contents:
            return None

        image = self.get_og_field("image")

        if image and image.find("https://") == -1:
            image = BasePage.get_url_full(self.url, image)

        return image

    @lazy_load_content
    def get_language(self):
        if not self.contents:
            return ""

        html = self.soup.find("html")
        if html and html.has_attr("lang"):
            return html["lang"]

        return ""

    @lazy_load_content
    def get_charset(self):
        if not self.contents:
            return None

        charset = None

        allmeta = self.soup.findAll("meta")
        for meta in allmeta:
            if "charset" in meta.attrs:
                return meta.attrs["charset"]

    @lazy_load_content
    def get_author(self):
        if not self.contents:
            return None

        return self.get_meta_field("author")

    def get_album(self):
        return None

    @lazy_load_content
    def get_favicons(self, recursive=False):
        if not self.contents:
            return []

        favicons = []

        link_finds = self.soup.find_all("link", attrs={"rel": "icon"})

        for link_find in link_finds:
            if link_find and link_find.has_attr("href"):
                full_favicon = link_find["href"]
                if full_favicon.strip() == "":
                    continue
                full_favicon = BasePage.get_url_full(self.url, full_favicon)
                if "sizes" in link_find:
                    favicons.append([full_favicon, link_find["sizes"]])
                else:
                    favicons.append([full_favicon, ""])

        link_finds = self.soup.find_all("link", attrs={"rel": "shortcut icon"})

        for link_find in link_finds:
            if link_find and link_find.has_attr("href"):
                full_favicon = link_find["href"]
                if full_favicon.strip() == "":
                    continue
                full_favicon = BasePage.get_url_full(self.url, full_favicon)
                if "sizes" in link_find:
                    favicons.append([full_favicon, link_find["sizes"]])
                else:
                    favicons.append([full_favicon, ""])

        return favicons

    @lazy_load_content
    def get_tags(self):
        if not self.contents:
            return None

        return self.get_meta_field("keywords")

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

    @lazy_load_content
    def get_rss_urls(self, full_check=False):
        if not self.contents:
            return []

        rss_links = (
            self.find_feed_links("application/rss+xml")
            + self.find_feed_links("application/atom+xml")
            + self.find_feed_links("application/rss+xml;charset=UTF-8")
        )

        if not rss_links:
            links = self.get_links_inner()
            rss_links.extend(
                link
                for link in links
                if "feed" in link or "rss" in link or "atom" in link
            )

        feed_url = self.url + "/feed"
        if full_check and feed_url not in rss_links:
            lucky_shot = self.url + "/feed"
            try:
                parser = RssPage(lucky_shot)
                feed = parser.parse()
                if feed.entries:
                    rss_links.append(lucky_shot)
            except Exception as e:
                LinkDatabase.info(
                    "WebTools exception during rss processing {}".format(str(e))
                )

        return (
            [BasePage.get_url_full(self.url, rss_url) for rss_url in rss_links]
            if rss_links
            else []
        )

    def find_feed_links(self, feed_type):
        feed_finds = self.soup.find_all("link", attrs={"type": feed_type})
        return [
            feed_find["href"]
            for feed_find in feed_finds
            if feed_find and feed_find.has_attr("href")
        ]

    @lazy_load_content
    def get_links(self):
        p = ContentLinkParser(self.url, self.contents)
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return links

    @lazy_load_content
    def get_links_inner(self):
        p = ContentLinkParser(self.url, self.contents)
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return ContentLinkParser.filter_link_in_domain(links, self.get_domain())

    @lazy_load_content
    def get_links_outer(self):
        p = ContentLinkParser(self.url, self.contents)
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        in_domain = ContentLinkParser.filter_link_in_domain(
            p.get_links(), self.get_domain()
        )
        return links - in_domain

    @lazy_load_content
    def get_domains(self):
        p = ContentLinkParser(self.url, self.contents)
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

    @lazy_load_content
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
        props["favicons"] = self.get_favicons()
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

        if self.get_date_published() != None:
            rating += 3

        if image_og:
            rating += 5

        rating = rating * 100 / self.get_max_page_rating()
        return int(rating)

    def get_max_page_rating(self):
        return 10 + 10 + 5 + 5 + 10 + 5 + 1 + 1 + 3 + 5

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

    @lazy_load_content
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
        if super().is_valid() == False:
            return False

        title = self.get_title()
        if title:
            title = title.lower()

        is_title_invalid = title and (
            title.find("forbidden") >= 0
            or title.find("access denied") >= 0
            or title.find("site not found") >= 0
            or title.find("page not found") >= 0
            or title.find("404 not found") >= 0
            or title.find("error 404") >= 0
        )

        if is_title_invalid:
            LinkDatabase.info("Title is invalid {}".format(title))
            return False

        return True


class Url(object):
    def get(url, contents=None, fast_check=True, options=None):
        """
        @note It is supposed to be more smart. Therefore for walled gardens it will
        decide about selenium.

        @returns Appropriate handler for the link
        """

        if options:
            fast_check = options.fast_parsing

        p = HtmlPage(url, contents=contents, options=options)

        if p.is_html(fast_check):
            return p

        if p.is_rss(fast_check):
            return RssPage(url, page_obj=p)

        if fast_check == False:
            j = JsonPage(url, page_obj=p)
            if j.is_json():
                return j

        return DefaultContentPage(url, page_obj=p)

    def get_favicon(url):
        page = Url.get(url)
        if not page:
            return

        if page.is_html():
            favs = page.get_favicons()
            if favs and len(favs) > 0:
                return favs[0][0]

        if not page.is_domain():
            dom = page.get_domain()
            page = Url.get(dom)
            if page.is_html():
                favs = page.get_favicons()
                if favs and len(favs) > 0:
                    return favs[0][0]

    def is_web_link(url):
        if (
            url.startswith("http")
            or url.startswith("//")
            or url.startswith("smb:")
            or url.startswith("ftp:")
        ):
            return True

        return False


class InputContent(object):
    def __init__(self, text):
        self.text = text

    def htmlify(self):
        """
        Use iterative approach. There is one thing to keep in mind:
         - text can contain <a href=" links already

        So some links needs to be translated. Some do not.

        @return text with https links changed into real links
        """
        self.text = self.strip_html_attributes()
        self.text = self.linkify("https://")
        self.text = self.linkify("http://")
        return self.text

    def strip_html_attributes(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(self.text, "html.parser")

        for tag in soup.find_all(True):
            if tag.name == "a":
                # Preserve "href" attribute for anchor tags
                tag.attrs = {"href": tag.get("href")}
            elif tag.name == "img":
                # Preserve "src" attribute for image tags
                tag.attrs = {"src": tag.get("src")}
            else:
                # Remove all other attributes
                tag.attrs = {}

        self.text = str(soup)
        return self.text

    def linkify(self, protocol="https://"):
        """
        @return text with https links changed into real links
        """
        if self.text.find(protocol) == -1:
            return self.text

        import re

        result = ""
        i = 0

        while i < len(self.text):
            pattern = r"{}\S+(?![\w.])".format(protocol)
            match = re.match(pattern, self.text[i:])
            if match:
                url = match.group()
                # Check the previous 10 characters
                preceding_chars = self.text[max(0, i - 10) : i]

                # We do not care who write links using different char order
                if '<a href="' not in preceding_chars and "<img" not in preceding_chars:
                    result += f'<a href="{url}">{url}</a>'
                else:
                    result += url
                i += len(url)
            else:
                result += self.text[i]
                i += 1

        self.text = result

        return result
