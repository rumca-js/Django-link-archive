"""
#1
Do not harm anyone. Write ethical programs, and scrapers.

#2
By default SSL verification is disabled. Speeds up processing. At least in my experience.

SSL is mostly important for interacting with pages, not when web scraping. I think. I am not an expert.

#3
If SSL verification is disabled you can see contents of your own domain:
https://support.bunny.net/hc/en-us/articles/360017484759-The-CDN-URLs-are-returning-redirects-back-to-my-domain

Other notes:
 - Sometimes we see the CDN URLs return a 301 redirect back to your own website.
   Usually, when this happens, it's caused by a misconfiguration of your origin server and the origin URL of your pull zone. If the origin URL sends back a redirect, our servers will simply forward that to the user.
 - 403 status code means that your user agent is incorrect / prohibited
 - other statuses can also mean that your user agent is rejected (rarely / edge cases)
 - content-type in headers can be incorrectly set. Found one RSS file that had "text/html"
 - I rely on tools. Those tools have problems/issues. Either we can live with that, or you would have to implement every dependency

TODO:
    - selenium and other drivers should be created once, then only asked for urls. Currently they are re-created each time we ask for a page
    - currently there is a hard limit for file size. If page is too big, it is just skipped
    - we should check meta info before obtaining entire file. Currently it is not done so. Encoding may be read from file, in some cases
    - maybe lists of mainstream media, or link services could be each in one class. Configurable, so that it can be overriden

Main classes are:
    - Url - most things should be done through it
    - PageOptions - upper layers should decide how a page should be called. Supplied to Url
    - PageResponseObject - page response, interface for all implementations
"""

import hashlib
import html
import traceback
import re
import json
import subprocess
from datetime import datetime, timedelta
from dateutil import parser

import requests

import html
import urllib.request, urllib.error, urllib.parse
import urllib.robotparser

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

# import chardet
from bs4 import BeautifulSoup

from .dateutils import DateUtils

selenium_feataure_enabled = True

try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.common.exceptions import TimeoutException

    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
except Exception as E:
    print(str(E))
    selenium_feataure_enabled = False


PAGE_TOO_BIG_BYTES = 5000000  # 5 MB. There are some RSS more than 1MB


URL_TYPE_RSS = "rss"
URL_TYPE_CSS = "css"
URL_TYPE_JAVASCRIPT = "javascript"
URL_TYPE_HTML = "html"
URL_TYPE_FONT = "font"
URL_TYPE_UNKNOWN = "unknown"

HTTP_STATUS_CODE_EXCEPTION = 600
HTTP_STATUS_CODE_CONNECTION_ERROR = 603
HTTP_STATUS_CODE_TIMEOUT = 604
HTTP_STATUS_CODE_FILE_TOO_BIG = 612
HTTP_STATUS_CODE_PAGE_UNSUPPORTED = 613


class WebLogger(object):
    web_logger = None

    def info(info_text, detail_text="", user=None, stack=False):
        if WebLogger.web_logger:
            WebLogger.web_logger.info(info_text, detail_text, user, stack)

    def debug(info_text, detail_text="", user=None, stack=False):
        if WebLogger.web_logger:
            WebLogger.web_logger.debug(info_text, detail_text, user, stack)

    def warning(info_text, detail_text="", user=None, stack=False):
        if WebLogger.web_logger:
            WebLogger.web_logger.warning(info_text, detail_text, user, stack)

    def error(info_text, detail_text="", user=None, stack=False):
        if WebLogger.web_logger:
            WebLogger.web_logger.error(info_text, detail_text, user, stack)

    def notify(info_text, detail_text="", user=None):
        if WebLogger.web_logger:
            WebLogger.web_logger.notify(info_text, detail_text, user, stack)

    def exc(exception_object, info_text=None, user=None):
        if WebLogger.web_logger:
            WebLogger.web_logger.exc(exception_object, info_text)


def lazy_load_content(func):
    """
    Lazy load for functions.
    We do not want page contents during construction.
    We want it only when necessary.
    """

    def wrapper(self, *args, **kwargs):
        if not self.response:
            self.response = self.get_response()
        return func(self, *args, **kwargs)

    return wrapper


def date_str_to_date(date_str):
    from .dateutils import DateUtils

    if date_str:
        wh = date_str.find("Published:")
        if wh >= 0:
            wh = date_str.find(":", wh)
            date_str = date_str[wh + 1 :].strip()

        try:
            parsed_date = parser.parse(date_str)
            return DateUtils.to_utc_date(parsed_date)
        except Exception as E:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            # we want to know who generated this issue
            detail_text = "Exception Data:{}\nStack:{}".format(str(E), stack_str)

            WebLogger.info(
                "Could not parse date:{}\n".format(date_str),
                detail_text=detail_text,
            )


def calculate_hash(text):
    try:
        return hashlib.md5(text.encode("utf-8")).digest()
    except Exception as E:
        WebLogger.exc(E, "Could not calculate hash")


class DomainAwarePage(object):
    def __init__(self, url):
        self.url = url

    def is_web_link(self):
        if (
            self.url.startswith("http://")
            or self.url.startswith("https://")
            or self.url.startswith("smb://")
            or self.url.startswith("ftp://")
            or self.url.startswith("//")
        ):
            # https://mailto is not a good link
            if self.url.find(".") == -1:
                return False

            return True

        return False

    def get_protocolless(self):
        protocol_pos = self.url.find("://")
        if protocol_pos >= 0:
            return self.url[protocol_pos + 3 :]

        return self.url

    def get_full_url(self):
        if self.url.lower().find("http") == -1:
            return "https://" + self.url
        return self.url

    def get_protocol_url(self, protocol="https"):
        """
        replaces any protocol with input protocol
        """
        protocol_pos = self.url.find("://")
        if protocol_pos >= 0:
            return protocol + "://" + self.url[protocol_pos + 3 :]

        return self.url

    def parse_url(self):
        """
        We cannot use urlparse, as it does not work with ftp:// or smb:// or win location
        returns tuple [protocol, separator, url]
        """
        if not self.url:
            return

        protocol_pos = self.url.find("://")
        if protocol_pos >= 0:
            return self.parse_protocoled_url()

        elif self.url.startswith("//"):
            return self.parse_netloc("//")
        elif self.url.startswith("\\\\"):
            return self.parse_netloc("\\\\")

        else:
            return ["https", "://", self.url]

    def parse_protocoled_url(self):
        protocol_pos = self.url.find("://")
        if protocol_pos >= 0:
            rest = self.url[protocol_pos + 3 :]
            protocol = self.url[:protocol_pos].lower()

            rest_data = self.parse_location(rest)

            if len(rest_data) > 1:
                arg = self.parse_argument(rest_data[1])
                return [protocol, "://", rest_data[0], arg[0], arg[1]]
            else:
                return [protocol, "://", rest_data[0]]

    def parse_netloc(self, separator="//"):
        """
        returns [domain, separator, rest of the link]
        """
        if self.url.startswith(separator):
            if separator == "//":
                lesser_separator = "/"
            else:
                lesser_separator = "\\"

            rest = self.url[len(separator) :]

            rest_data = self.parse_location(rest)

            if len(rest_data) > 1:
                arg = self.parse_argument(rest_data[1])
                return ["", separator, rest_data[0], arg[0], arg[1]]
            else:
                return ["", separator, rest_data[0]]

    def parse_location(self, rest):
        """
        returns tuple [link, arguments]
        """
        wh1 = rest.find("/")
        wh2 = rest.find("\\")
        wh3 = rest.find("?")
        wh4 = rest.find("#")
        positions = [wh for wh in [wh1, wh2, wh3, wh4] if wh != -1]

        if len(positions) > 0:
            smallest_position = min(positions)
            return [rest[:smallest_position], rest[smallest_position:]]
        return [rest, ""]

    def parse_argument(self, rest):
        """
        returns tuple [link, arguments]
        """
        wh1 = rest.find("?")
        wh2 = rest.find("#")
        positions = [wh for wh in [wh1, wh2] if wh != -1]

        if len(positions) > 0:
            smallest_position = min(positions)
            return [rest[:smallest_position], rest[smallest_position:]]
        return [rest, ""]

    def get_domain(self):
        """
        for https://domain.com/test

        @return https://domain.com
        """
        if not self.url:
            return

        parts = self.parse_url()

        wh = parts[2].find(":")
        if wh >= 0:
            parts[2] = parts[2][:wh]

        text = parts[0] + parts[1] + parts[2].lower()
        x = DomainAwarePage(text)
        if self.url and not x.is_web_link():
            return

        # if passed email, with user
        wh = text.find("@")
        if wh >= 0:
            return parts[0] + parts[1] + text[wh + 1 :]

        return text

    def get_domain_only(self):
        """
        for https://domain.com/test

        @return domain.com
        """
        parts = self.parse_url()
        if parts:
            return parts[2].lower()

    def get_scheme(self):
        parts = self.parse_url()
        if parts:
            return parts[0]

    def is_domain(self):
        if not self.url:
            return False

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
        if url.lower().find("http") == 0:
            ready_url = url
        else:
            if url.startswith("//"):
                ready_url = "https:" + url
            elif url.startswith("/"):
                domain = DomainAwarePage(domain).get_domain()
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

    def up(self, skip_internal=False):
        if self.is_domain():
            return self.up_domain()
        else:
            if skip_internal:
                domain = self.get_domain()
                return DomainAwarePage(domain)
            return self.up_not_domain()

    def up_domain(self):
        """
        https://github.com
        """
        domain = self.url
        if domain.count(".") == 1:
            return None

        else:
            parts = self.parse_url()
            if len(parts) < 3:
                return

            sp = parts[2].split(".")
            url = parts[0] + parts[1] + ".".join(sp[1:])
            return DomainAwarePage(url)

    def up_not_domain(self):
        url = self.url
        wh = self.url.rfind("/")
        if wh >= 0:
            return DomainAwarePage(self.url[:wh])

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

        if not url:
            return False

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

        if not url:
            return False

        if url.find("lmg.gg") >= 0:
            return True
        if url.find("geni.us") >= 0:
            return True
        if url.find("tinyurl.com") >= 0:
            return True
        if url.find("bit.ly") >= 0:
            return True
        if url.find("ow.ly") >= 0:
            return True
        if url.find("adfoc.us") >= 0:
            return True
        if url.endswith("link.to"):
            return True
        if url.find("mailchi.mp") >= 0:
            return True
        if url.find("dbh.la") >= 0:
            return True
        if url.find("ffm.to") >= 0:
            return True
        if url.find("kit.co") >= 0:
            return True
        if url.find("utm.io") >= 0:
            return True
        if url.find("tiny.pl") >= 0:
            return True
        if url.find("reurl.cc") >= 0:
            return True

        # shortcuts
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

    def is_media(self):
        """
        TODO - crude, hardcoded
        """
        ext = self.get_page_ext()
        if not ext:
            return False

        ext_mapping = [
            "mp3",
            "mp4",
            "avi",
            "ogg",
            "flac",
            "rmvb",
            "wmv",
            "wma",
        ]

        return ext in ext_mapping

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

        return ext

    def get_type_by_ext(self):
        """
        TODO - crude, hardcoded
        """
        if self.is_analytics():
            return

        ext_mapping = {
            "css": URL_TYPE_CSS,
            "js": URL_TYPE_JAVASCRIPT,
            "html": URL_TYPE_HTML,
            "htm": URL_TYPE_HTML,
            "php": URL_TYPE_HTML,
            "aspx": URL_TYPE_HTML,
            "woff2": URL_TYPE_FONT,
            "tff": URL_TYPE_FONT,
        }

        ext = self.get_page_ext()
        if ext:
            if ext in ext_mapping:
                return ext_mapping[ext]

        # if not found, we return none

    def get_robots_txt_url(self):
        return self.get_domain() + "/robots.txt"

    def is_link_in_domain(self, address):
        if not address.startswith(self.get_domain()):
            return False
        return True

    def split(self):
        result = []
        parts = self.parse_url()

        if len(parts) > 2:
            result.append(parts[0] + parts[1] + parts[2])
        if len(parts) > 3:
            for part in parts[3:]:
                result.append(part)

        return result

    def join(self, parts):
        result = ""

        for part in parts:
            if result.endswith("/"):
                result = result[:-1]
            if part.startswith("/"):
                part = part[1:]

            if part.startswith("?") or part.startswith("#"):
                result = result + part
            else:
                result = result + "/" + part

        return result


class ContentInterface(object):
    def __init__(self, url, contents):
        self.url = url
        self.contents = contents

    def get_contents(self):
        return self.contents

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
        Default behavior
        """
        rating_vector = self.get_page_rating_vector()
        link_rating = self.get_link_rating()
        rating_vector.extend(link_rating)

        page_rating = 0
        max_page_rating = 0
        for rating in rating_vector:
            page_rating += rating[0]
            max_page_rating += rating[1]

        if page_rating == 0:
            return 0
        if max_page_rating == 0:
            return 0

        page_rating = (float(page_rating) * 100.0) / float(max_page_rating)

        return int(page_rating)

    def get_page_rating_vector(self):
        """
        Returns vector of tuples.
        Each tuple contains actual rating for property, and max rating for that property
        """
        result = []

        if self.get_title() is not None and str(self.get_title()) != "":
            result.append([10, 10])

        if self.get_description() is not None and str(self.get_description()) != "":
            result.append([5, 5])

        if self.get_language() is not None and str(self.get_language()) != "":
            result.append([1, 1])

        if self.get_thumbnail() is not None and str(self.get_thumbnail()) != "":
            result.append([1, 1])

        if (
            self.get_date_published() is not None
            and str(self.get_date_published()) != ""
        ):
            result.append([1, 1])

        return result

    def get_date_published(self):
        """
        This should be date. Not string
        """
        raise NotImplementedError

    def get_contents_hash(self):
        contents = self.get_contents()
        if contents:
            return calculate_hash(contents)

    def get_contents_body_hash(self):
        return self.get_contents_hash()

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
        """
        Should not obtain contents by itself
        """
        contents = self.contents

        if contents:
            if (
                contents.find("https://static.cloudflareinsights.com/beacon.min.js/")
                >= 0
            ):
                return True
            if contents.find("https://challenges.cloudflare.com") >= 0:
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

        # elif year:
        #    current_year = int(datetime.now().year)

        #    if year >= current_year or year < 1900:
        #        date_object = datetime.now()
        #    else:
        #        # If only the year is found, construct a datetime object with year
        #        date_object = datetime(year, 1, 1)

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
            WebLogger.debug("Error:{}".format(str(E)))

        if not month_number:
            try:
                month_number = strptime(month, "%b").tm_mon
                month_number = str(month_number)
            except Exception as E:
                WebLogger.debug("Error:{}".format(str(E)))

        if not month_number:
            try:
                month_number = strptime(month, "%B").tm_mon
                month_number = str(month_number)
            except Exception as E:
                WebLogger.debug("Error:{}".format(str(E)))

        if month_number is None:
            WebLogger.debug(
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
            WebLogger.debug(
                "Guessing date error: URL:{};\nYear:{};\nMonth:{}\nDay:{}".format(
                    self.url, year, month, day
                )
            )

    def get_position_of_html_tags(self):
        if not self.contents:
            return -1

        lower = self.contents.lower()
        if lower.find("<html") >= 0 and lower.find("<body") >= 0:
            return lower.find("<html")

        lower = self.contents.lower()
        if lower.find("<html") >= 0 and lower.find("<meta") >= 0:
            return lower.find("<html")

        return -1

    def get_position_of_rss_tags(self):
        if not self.contents:
            return -1

        lower = self.contents.lower()
        if lower.find("<rss") >= 0 and lower.find("<channel") >= 0:
            return lower.find("<rss")
        if lower.find("<feed") >= 0 and lower.find("<entry") >= 0:
            return lower.find("<feed")
        if lower.find("<rdf") >= 0 and lower.find("<channel") >= 0:
            return lower.find("<rdf")

        return -1

    def get_link_rating(self):
        rating = []

        if self.url.startswith("https://"):
            rating.append([1, 1])
        elif self.url.startswith("ftp://"):
            rating.append([1, 1])
        elif self.url.startswith("smb://"):
            rating.append([1, 1])
        elif self.url.startswith("http://"):
            rating.append([0, 1])
        else:
            rating.append([0, 1])

        p = DomainAwarePage(self.url)
        if p.is_domain():
            rating.append([1, 1])

        domain_only = p.get_domain_only()
        if domain_only.count(".") == 1:
            rating.append([2, 2])
        elif domain_only.count(".") == 2:
            rating.append([1, 2])
        else:
            rating.append([0, 2])

        # as example https://www.youtube.com has 23 chars

        if len(self.url) < 25:
            rating.append([2, 2])
        elif len(self.url) < 30:
            rating.append([1, 2])
        else:
            rating.append([0, 2])

        return rating


class DefaultContentPage(ContentInterface):
    def __init__(self, url, contents=""):
        super().__init__(url=url, contents=contents)

    def get_title(self):
        return None

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
        """
        This should be date. Not string
        """
        return None

    def is_valid(self):
        return True

    def get_response(self):
        return ""


class JsonPage(ContentInterface):
    def __init__(self, url, contents):
        super().__init__(url=url, contents=contents)

        self.json_obj = None
        try:
            contents = self.get_contents()
            self.json_obj = json.loads(contents)
        except Exception as e:
            # to be expected
            WebLogger.debug("Invalid json:{}".format(contents))

    def is_valid(self):
        if self.json_obj:
            return True

    def get_title(self):
        if self.json_obj and "title" in self.json_obj:
            return str(self.json_obj["title"])

    def get_description(self):
        if self.json_obj and "description" in self.json_obj:
            return str(self.json_obj["description"])

    def get_language(self):
        if self.json_obj and "language" in self.json_obj:
            return str(self.json_obj["language"])

    def get_thumbnail(self):
        if self.json_obj and "thumbnail" in self.json_obj:
            return str(self.json_obj["thumbnail"])

    def get_author(self):
        if self.json_obj and "author" in self.json_obj:
            return str(self.json_obj["author"])

    def get_album(self):
        if self.json_obj and "album" in self.json_obj:
            return str(self.json_obj["album"])

    def get_tags(self):
        if self.json_obj and "tags" in self.json_obj:
            return str(self.json_obj["tags"])

    def get_date_published(self):
        if self.json_obj and "date_published" in self.json_obj:
            return date_str_to_date(self.json_obj["date_published"])

    def get_page_rating(self):
        return 0


class RssPageEntry(ContentInterface):
    def __init__(self, feed_index, feed_entry, url, contents, page_object_properties):
        self.feed_index = feed_index
        self.feed_entry = feed_entry
        self.url = url
        self.contents = contents
        self.page_object_properties = page_object_properties

        super().__init__(url=self.url, contents=contents)

        self.allow_adding_with_current_time = True
        self.default_entry_timestamp = None

    def get_properties(self):
        """
        """
        output_map = {}

        link = None

        if "link" in self.feed_entry:
            if self.feed_entry.link != "":
                link = self.feed_entry.link
            else:
                link = self.try_to_extract_link()

        if not link:
            return output_map

        link = link.strip()

        output_map = super().get_properties()

        output_map["link"] = link
        output_map["source"] = self.url
        output_map["bookmarked"] = False
        output_map["feed_entry"] = self.feed_entry

        return output_map

    def try_to_extract_link(self):
        """
        For:
         - https://thehill.com/feed
         - https://warhammer-community.com/feed

        feedparser provide empty links
        Trying to work around that issue.

        RSS can have <entry, or <item things inside

        TODO this should be parsed using beautiful soup
        """
        contents = self.contents

        item_search_wh = contents.find("<item", 0)
        entry_search_wh = contents.find("<entry", 0)

        index = 0
        wh = 0
        while index <= self.feed_index:
            if item_search_wh >= 0:
                wh = contents.find("<item", wh+1)
                if wh == -1:
                    return
            if entry_search_wh >= 0:
                wh = contents.find("<entry", wh+1)
                if wh == -1:
                    return

            index += 1

        wh = contents.find("<link", wh+1)
        if wh == -1:
            return

        wh = contents.find(">", wh+1)
        if wh == -1:
            return

        wh2 = contents.find("<", wh+1)
        if wh2 == -1:
            return

        text = contents[wh+1 : wh2]

        return text

    def get_title(self):
        return self.feed_entry.title

    def get_description(self):
        if hasattr(self.feed_entry, "description"):
            return self.feed_entry.description
        else:
            return ""

    def get_thumbnail(self):
        if hasattr(self.feed_entry, "media_thumbnail"):
            if len(self.feed_entry.media_thumbnail) > 0:
                thumb = self.feed_entry.media_thumbnail[0]
                if "url" in thumb:
                    return thumb["url"]
                else:
                    return str(thumb)
        if hasattr(self.feed_entry, "media_content"):
            if len(self.feed_entry.media_content) > 0:
                thumb = self.feed_entry.media_content[0]
                if "url" in thumb:
                    return thumb["url"]
                else:
                    return str(thumb)

        return None

    def get_language(self):
        if "language" in self.page_object_properties:
            return self.page_object_properties["language"]

    def get_date_published(self):
        date = self.get_date_published_implementation()

        from .dateutils import DateUtils

        if date > DateUtils.get_datetime_now_utc():
            date = DateUtils.get_datetime_now_utc()

        return date

    def get_date_published_implementation(self):
        from .dateutils import DateUtils

        if hasattr(self.feed_entry, "published"):
            if str(self.feed_entry.published) == "":
                return DateUtils.get_datetime_now_utc()
            else:
                try:
                    dt = parser.parse(self.feed_entry.published)
                    return DateUtils.to_utc_date(dt)

                except Exception as e:
                    WebLogger.error(
                        "RSS parser {} datetime invalid feed datetime:{};\nFeed DateTime:{};\nExc:{}\n".format(
                            self.url,
                            self.feed_entry.published,
                            self.feed_entry.published,
                            str(e),
                        )
                    )
                return DateUtils.get_datetime_now_utc()

        elif self.allow_adding_with_current_time:
            return DateUtils.get_datetime_now_utc()
        elif self.default_entry_timestamp:
            return self.default_entry_timestamp
        else:
            return DateUtils.get_datetime_now_utc()

    def get_author(self):
        if "author" in self.page_object_properties:
            return self.page_object_properties["author"]

    def get_album(self):
        return ""

    def get_tags(self):
        if "tags" in self.feed_entry:
            return self.feed_entry.tags

        return None


class RssPage(ContentInterface):
    """
    Handles RSS parsing.
    Do not use feedparser directly enywhere. We use BasicPage
    which allows to define timeouts.
    """

    def __init__(self, url, contents):
        self.feed = None

        """
        Workaround for https://warhammer-community.com/feed
        """
        if contents:
            wh = contents.find("<rss version")
            if wh > 0:
                contents = contents[wh:]

        super().__init__(url=url, contents=contents)

        if self.contents and not self.feed:
            self.process_contents()

    def process_contents(self):
        contents = self.contents
        if contents is None:
            return None

        try:
            import feedparser

            self.feed = feedparser.parse(contents)
            return self.feed

        except Exception as E:
            WebLogger.exc(E, "Url:{}. RssPage, when parsing.".format(self.url))

    def get_container_elements(self):
        if self.feed is None:
            return

        try:
            for item in self.get_container_elements_maps():
                yield item

        except Exception as E:
            WebLogger.exc(E, "Url:{}. RSS parsing error".format(self.url))

    def get_container_elements_maps(self):
        parent_properties = self.get_properties()
        contents = self.get_contents()

        for feed_index, feed_entry in enumerate(self.feed.entries):
            rss_entry = RssPageEntry(
                feed_index,
                feed_entry,
                self.url,
                contents,
                parent_properties,
            )
            entry_props = rss_entry.get_properties()

            if not entry_props:
                WebLogger.debug(
                    "No properties for feed entry:{}".format(str(feed_entry))
                )
                continue

            if "link" not in entry_props or entry_props["link"] is None:
                WebLogger.error(
                    "Url:{}. Missing link in RSS".format(self.url),
                    detail_text=str(feed_entry),
                )
                continue

            yield entry_props

    def get_contents_body_hash(self):
        if not self.contents:
            return

        #    WebLogger.error("No rss hash contents")
        #    return calculate_hash("no body hash")

        entries = str(self.feed.entries)
        if entries == "":
            if self.contents:
                return calculate_hash(self.contents)
        if entries:
            return calculate_hash(entries)

    def get_title(self):
        if self.feed is None:
            return

        if "title" in self.feed.feed:
            return self.feed.feed.title

    def get_description(self):
        if self.feed is None:
            return

        if "subtitle" in self.feed.feed:
            return self.feed.feed.subtitle

        if "description" in self.feed.feed:
            return self.feed.feed.description

    def get_language(self):
        if self.feed is None:
            return

        if "language" in self.feed.feed:
            return self.feed.feed.language

    def get_thumbnail(self):
        if self.feed is None:
            return

        image = None
        if "image" in self.feed.feed:
            if "href" in self.feed.feed.image:
                try:
                    image = str(self.feed.feed.image["href"])
                except Exception as E:
                    WebLogger.debug(str(E))

            elif "url" in self.feed.feed.image:
                try:
                    image = str(self.feed.feed.image["url"])
                except Exception as E:
                    WebLogger.debug(str(E))
            elif "links" in self.feed.feed.image:
                links = self.feed.feed.image["links"]
                if len(links) > 0:
                    if "type" in links[0]:
                        if links[0]["type"] == "text/html":
                            pass
                            # normal scenario, no worries
                        else:
                            WebLogger.error(
                                '<a href="{}">{}</a> Unsupported image type for feed. Image:{}'.format(
                                    self.url, self.url, str(self.feed.feed.image)
                                )
                            )
            else:
                WebLogger.error(
                    '<a href="{}">{}</a> Unsupported image type for feed. Image:{}'.format(
                        self.url, self.url, str(self.feed.feed.image)
                    )
                )

        # TODO that does not work
        # if not image:
        #    if self.url.find("https://www.youtube.com/feeds/videos.xml") >= 0:
        #        image = self.get_thumbnail_manual_from_youtube()

        if image and image.lower().find("https://") == -1:
            image = DomainAwarePage.get_url_full(self.url, image)

        return image

    def get_thumbnail_manual_from_youtube(self):
        if "link" in self.feed.feed:
            link = self.feed.feed.link
            p = RequestBuilder(link)
            p = HtmlPage(link, p.get_contents())
            return p.get_thumbnail()

    def get_author(self):
        if self.feed is None:
            return

        if "author" in self.feed.feed:
            return self.feed.feed.author

    def get_album(self):
        if self.feed is None:
            return

        return None

    def get_date_published(self):
        if self.feed is None:
            return

        if "published" in self.feed.feed:
            return date_str_to_date(self.feed.feed.published)

    def get_tags(self):
        if self.feed is None:
            return

        if "tags" in self.feed.feed:
            return self.feed.feed.tags

        return None

    def get_properties(self):
        props = super().get_properties()
        props["contents"] = self.get_contents()
        return props

    def is_valid(self):
        if self.feed and len(self.feed.entries) > 0:
            return True

        # if not self.is_contents_rss():
        #     return False

        return True

    def is_contents_rss(self):
        """
        We want the checks to be simple yet effective. Check some tokens.

        There can be RSS sources in HTML, HTML inside RSS. Beware
        """
        if not self.contents:
            return

        #html_tags = self.get_position_of_html_tags()
        rss_tags = self.get_position_of_rss_tags()

        #if html_tags >= 0 and rss_tags >= 0:
        #    return rss_tags < html_tags
        if rss_tags >= 0:
            return True

    def get_charset(self):
        """
        TODO read from encoding property of xml
        """
        if not self.contents:
            return None

        if self.contents.find("encoding") >= 0:
            return "utf-8"


class ContentLinkParser(ContentInterface):
    """
    TODO filter also html from non html
    """

    def __init__(self, url, contents):
        super().__init__(url=url, contents=contents)
        self.url = DomainAwarePage(url).get_clean_url()

    def get_links(self):
        links = set()

        links.update(self.get_links_https("https"))
        links.update(self.get_links_https_encoded("https"))
        links.update(self.get_links_https("http"))
        links.update(self.get_links_https_encoded("http"))
        links.update(self.get_links_href())

        # This is most probably redundant
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
            if DomainAwarePage(link).is_web_link():
                result.add(link)

        return links

    def get_links_https(self, protocol="https"):
        cont = str(self.get_contents())

        pattern = "(" + protocol + "?://[a-zA-Z0-9./\-_?&=#;:]+)"

        all_matches = re.findall(pattern, cont)
        # links cannot end with "."
        all_matches = [link.rstrip(".") for link in all_matches]
        return set(all_matches)

    def get_links_https_encoded(self, protocol="https"):
        cont = str(self.get_contents())

        pattern = "(" + protocol + "?:&#x2F;&#x2F;[a-zA-Z0-9./\-_?&=#;:]+)"

        all_matches = re.findall(pattern, cont)
        # links cannot end with "."
        all_matches = [link.rstrip(".") for link in all_matches]
        all_matches = [ContentLinkParser.decode_url(link) for link in all_matches]
        return set(all_matches)

    def join_url_parts(self, partone, parttwo):
        if not partone.endswith("/"):
            partone = partone + "/"
        if parttwo.startswith("/"):
            parttwo = parttwo[1:]

        return partone + parttwo

    def decode_url(url):
        return html.unescape(url)

    def get_links_href(self):
        links = set()

        url = self.url
        domain = DomainAwarePage(self.url).get_domain()

        cont = str(self.get_contents())

        all_matches = re.findall('href="([a-zA-Z0-9./\-_?&=@#;:]+)', cont)

        for item in all_matches:
            ready_url = None

            item = item.strip()

            # exclude mailto: tel: sms:
            pattern = "^[a-zA-Z0-9]+:"
            if re.match(pattern, item):
                if (
                    not item.startswith("http")
                    and not item.startswith("ftp")
                    and not item.startswith("smb")
                ):
                    wh = item.find(":")
                    item = item[wh + 1 :]

            if item.startswith("//"):
                if not item.startswith("http"):
                    item = "https:" + item

            if item.startswith("/"):
                item = self.join_url_parts(domain, item)

            # for urls like user@domain.com/location
            pattern = "^[a-zA-Z0-9]+@"
            if re.match(pattern, item):
                wh = item.find("@")
                item = item[wh + 1 :]

            # not absolute path
            if not (item.startswith("http") and not item.startswith("ftp")):
                if item.count(".") <= 0:
                    item = self.join_url_parts(url, item)
                else:
                    if not item.startswith("http"):
                        item = "https://" + item

            if item.startswith("https:&#x2F;&#x2F") or item.startswith(
                "http:&#x2F;&#x2F"
            ):
                item = ContentLinkParser.decode_url(item)

            if item:
                links.add(item)

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
            p = DomainAwarePage(link)
            new_link = p.get_domain()
            if new_link:
                result.add(new_link)

        return result

    def get_domains(self):
        links = self.get_links()
        links = ContentLinkParser.filter_domains(links)
        return links

    def get_links_inner(self):
        links = self.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return ContentLinkParser.filter_link_in_domain(
            links, DomainAwarePage(self.url).get_domain()
        )

    def get_links_outer(self):
        links = self.get_links()
        links = ContentLinkParser.filter_link_html(links)

        in_domain = ContentLinkParser.filter_link_in_domain(
            links, DomainAwarePage(self.url).get_domain()
        )
        return links - in_domain


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

    def __init__(self, url, contents):
        super().__init__(url=url, contents=contents)

        if self.contents:
            try:
                self.soup = BeautifulSoup(self.contents, "html.parser")
            except Exception as E:
                WebLogger.exc(E, "Contents type:{}".format(type(self.contents)))
                self.contents = None
                self.soup = None
        else:
            self.soup = None

    def get_head_field(self, field):
        if not self.contents:
            return None

        found_element = self.soup.find(field)
        if found_element:
            value = found_element.string
            if value != "":
                return value

    def get_meta_custom_field(self, field_type, field):
        if not self.contents:
            return None

        find_element = self.soup.find("meta", attrs={field_type: field})
        if find_element and find_element.has_attr("content"):
            return find_element["content"]

    def get_schema_field(self, itemprop):
        elements_with_itemprop = self.soup.find_all(attrs={"itemprop": True})
        for element in elements_with_itemprop:
            itemprop_v = element.get("itemprop")
            if itemprop_v != itemprop:
                continue

            if element.name == "link":
                value = element.get("href")
            elif element.name == "meta":
                value = element.get("content")
            else:
                value = element.text.strip() if element.text else None

            return value

    def get_schema_field_ex(self, itemtype, itemprop):
        """
        itemtype can be "http://schema.org/VideoObject"
        """
        # Find elements with itemtype="http://schema.org/VideoObject"
        video_objects = self.soup.find_all(attrs={"itemtype": itemtype})
        for video_object in video_objects:
            # Extract itemprop from elements inside video_object
            elements_with_itemprop = video_object.find_all(attrs={"itemprop": True})
            for element in elements_with_itemprop:
                itemprop_v = element.get("itemprop")

                if itemprop_v != itemprop:
                    continue

                if element.name == "link":
                    value = element.get("href")
                elif element.name == "meta":
                    value = element.get("content")
                else:
                    value = element.text.strip() if element.text else None

                return value

    def get_meta_field(self, field):
        if not self.contents:
            return None

        return self.get_meta_custom_field("name", field)

    def get_property_field(self, name):
        if not self.contents:
            return None

        field_find = self.soup.find("meta", property="{}".format(name))
        if field_find and field_find.has_attr("content"):
            return field_find["content"]

    def get_og_field(self, name):
        """
        Open Graph protocol: https://ogp.me/
        """
        if not self.contents:
            return None

        return self.get_property_field("og:{}".format(name))

    def get_title(self):
        if not self.contents:
            return None

        title = self.get_og_field("title")

        if not title:
            self.get_schema_field("name")

        if not title:
            title = self.get_title_meta()

        if not title:
            title = self.get_title_head()

        if not title:
            title = self.get_og_site_name()

        if title:
            title = title.strip()

            # TODO hardcoded. Some pages provide such a dumb title with redirect
            if title.find("Just a moment") >= 0:
                title = ""

        return title
        # title = html.unescape(title)

    def get_date_published(self):
        """
        There could be multiple places to read published time.
        We try every possible thing.
        """

        # used by mainstream media. Examples?
        date_str = self.get_property_field("article:published_time")
        if date_str:
            return date_str_to_date(date_str)

        # used by spotify
        date_str = self.get_meta_field("music:release_date")
        if date_str:
            return date_str_to_date(date_str)

        # used by youtube
        date_str = self.get_schema_field("datePublished")
        if date_str:
            return date_str_to_date(date_str)

    def get_title_head(self):
        if not self.contents:
            return None

        return self.get_head_field("title")

    def get_title_meta(self):
        if not self.contents:
            return None

        return self.get_meta_field("title")

    def get_description(self):
        if not self.contents:
            return None

        description = self.get_og_field("description")

        if not description:
            description = self.get_schema_field("description")

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

    def get_description_head(self):
        if not self.contents:
            return None

        return self.get_head_field("description")

    def get_description_meta(self):
        if not self.contents:
            return None

        return self.get_meta_field("description")

    def get_thumbnail(self):
        if not self.contents:
            return None

        image = self.get_og_field("image")

        if not image:
            image = self.get_schema_field("thumbnailUrl")

        # do not return favicon here.
        # we use thumbnails in <img, but icons do not work correctly there

        if image and image.lower().find("https://") == -1:
            image = DomainAwarePage.get_url_full(self.url, image)

        return image

    def get_language(self):
        if not self.contents:
            return ""

        html = self.soup.find("html")
        if html and html.has_attr("lang"):
            return html["lang"]

        locale = self.get_og_locale()
        if locale:
            return locale

        return ""

    def get_charset(self):
        if not self.contents:
            return None

        charset = None

        allmeta = self.soup.findAll("meta")
        for meta in allmeta:
            for attr in meta.attrs:
                if attr.lower() == "charset":
                    return meta.attrs[attr]
                if attr.lower() == "http-equiv":
                    if "content" in meta.attrs:
                        text = meta.attrs["content"].lower()
                        wh = text.find("charset")
                        if wh >= 0:
                            wh2 = text.find("=", wh)
                            if wh2 >= 0:
                                charset = text[wh2 + 1 :].strip()
                                return charset

    def get_author(self):
        """
        <head><author>Something</author></head>
        """
        if not self.contents:
            return None

        author = self.get_meta_field("author")
        if not author:
            author = self.get_og_field("author")

        return author

    def get_album(self):
        return None

    def get_favicons(self, recursive=False):
        if not self.contents:
            return {}

        favicons = {}

        link_finds = self.soup.find_all("link", attrs={"rel": "icon"})

        for link_find in link_finds:
            if link_find and link_find.has_attr("href"):
                full_favicon = link_find["href"]
                if full_favicon.strip() == "":
                    continue
                full_favicon = DomainAwarePage.get_url_full(self.url, full_favicon)
                if "sizes" in link_find:
                    favicons[full_favicon] = link_find["sizes"]
                else:
                    favicons[full_favicon] = ""

        link_finds = self.soup.find_all("link", attrs={"rel": "shortcut icon"})

        for link_find in link_finds:
            if link_find and link_find.has_attr("href"):
                full_favicon = link_find["href"]
                if full_favicon.strip() == "":
                    continue
                full_favicon = DomainAwarePage.get_url_full(self.url, full_favicon)
                if "sizes" in link_find:
                    favicons[full_favicon] = link_find["sizes"]
                else:
                    favicons[full_favicon] = ""

        return favicons

    def get_tags(self):
        if not self.contents:
            return None

        return self.get_meta_field("keywords")

    def get_og_title(self):
        return self.get_og_field("title")

    def get_og_description(self):
        return self.get_og_field("description")

    def get_og_site_name(self):
        return self.get_og_field("site_name")

    def get_og_image(self):
        return self.get_og_field("image")

    def get_og_locale(self):
        return self.get_og_field("locale")

    def get_rss_url(self, full_check=False):
        urls = self.get_rss_urls()
        if urls and len(urls) > 0:
            return urls[0]

    def get_rss_urls(self, full_check=False):
        if not self.contents:
            return []

        rss_links = self.find_feed_links("application/rss+xml") + self.find_feed_links(
            "application/atom+xml"
        )

        if not rss_links:
            links = self.get_links_inner()
            rss_links.extend(
                link
                for link in links
                if "feed" in link or "rss" in link or "atom" in link
            )

        return (
            [DomainAwarePage.get_url_full(self.url, rss_url) for rss_url in rss_links]
            if rss_links
            else []
        )

    def find_feed_links(self, feed_type):
        result_links = []

        found_elements = self.soup.find_all("link")
        for found_element in found_elements:
            if found_element.has_attr("type"):
                link_type = str(found_element["type"])
                if link_type.find(feed_type) >= 0:
                    if found_element.has_attr("href"):
                        result_links.append(found_element["href"])
                    else:
                        WebLogger.error(
                            "Found {} link without href. Str:{}".format(
                                feed_type, str(found_element)
                            )
                        )

        return result_links

    def get_links(self):
        p = ContentLinkParser(self.url, self.contents)
        links = p.get_links()
        links = ContentLinkParser.filter_link_html(links)
        return links

    def get_links_inner(self):
        p = ContentLinkParser(self.url, self.contents)
        return p.get_links_inner()

    def get_links_outer(self):
        p = ContentLinkParser(self.url, self.contents)
        return p.get_links_outer()

    def get_domains(self):
        p = ContentLinkParser(self.url, self.contents)
        return p.get_domains()

    def get_domain_page(self):
        if self.url == self.get_domain():
            return self

        return Page(self.get_domain())

    def get_properties(self):
        props = super().get_properties()

        props["meta_title"] = self.get_title_meta()
        props["meta_description"] = self.get_description_meta()
        props["og_title"] = self.get_og_title()
        props["og_description"] = self.get_og_description()
        props["og_site_name"] = self.get_og_site_name()
        props["og_locale"] = self.get_og_locale()
        props["og_image"] = self.get_og_image()
        # props["is_html"] = self.is_html()
        props["charset"] = self.get_charset()
        props["rss_urls"] = self.get_rss_urls()
        # props["status_code"] = self.status_code

        # if DomainAwarePage(self.url).is_domain():
        #    if self.is_robots_txt():
        #        props["robots_txt_url"] = DomainAwarePage(self.url).get_robots_txt_url()
        #        props["site_maps_urls"] = self.get_site_maps()

        props["links"] = self.get_links()
        props["links_inner"] = self.get_links_inner()
        props["links_outer"] = self.get_links_outer()
        props["favicons"] = self.get_favicons()
        props["contents"] = self.get_contents()
        if self.get_contents():
            props["contents_length"] = len(self.get_contents())

        return props

    def get_page_rating_vector(self):
        rating = []

        title_meta = self.get_title_meta()
        title_og = self.get_og_title()
        description_meta = self.get_description_meta()
        description_og = self.get_og_description()
        image_og = self.get_og_image()
        language = self.get_language()

        rating.append(self.get_page_rating_title(title_meta))
        rating.append(self.get_page_rating_title(title_og))
        rating.append(self.get_page_rating_description(description_meta))
        rating.append(self.get_page_rating_description(description_og))
        rating.append(self.get_page_rating_language(language))
        # rating.append(self.get_page_rating_status_code(self.response.status_code))

        if self.get_author() != None:
            rating.append([1, 1])
        if self.get_tags() != None:
            rating.append([1, 1])

        if self.get_date_published() != None:
            rating.append([3, 3])

        if image_og:
            rating.append([5, 5])

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

        return [rating, 10]

    def get_page_rating_description(self, description):
        rating = 0
        if description is not None:
            rating += 5

        return [rating, 5]

    def get_page_rating_language(self, language):
        rating = 0
        if language is not None:
            rating += 5
        if language.find("en") >= 0:
            rating += 1

        return [rating, 5]

    def is_valid(self):
        """
        This is a simple set of rules in which we reject the page:
         - status code
         - if valid HTML code
        """
        if not self.is_contents_html():
            return False

        return True

    def is_contents_html(self):
        """
        We want the checks to be simple yet effective. Check some tokens.

        There can be RSS sources in HTML, HTML inside RSS. Beware
        """
        if not self.contents:
            WebLogger.debug("Could not obtain contents for {}".format(self.url))
            return

        html_tags = self.get_position_of_html_tags()
        rss_tags = self.get_position_of_rss_tags()

        if html_tags >= 0 and rss_tags >= 0:
            return html_tags < rss_tags
        if html_tags >= 0:
            return True

    def get_body_text(self):
        if not self.contents:
            return

        body_find = self.soup.find("body")
        if not body_find:
            return

        return body_find.get_text()

    def get_contents_body_hash(self):
        if not self.contents:
            return

        body = self.get_body_text()

        if body == "":
            return
        elif body:
            return calculate_hash(body)
        else:
            WebLogger.error("HTML: Cannot calculate body hash for:{}".format(self.url))
            if self.contents:
                return calculate_hash(self.contents)

    def is_pwa(self):
        """
        @returns true, if it is progressive web app
        """
        if self.get_pwa_manifest():
            return True

    def get_pwa_manifest(self):
        link_finds = self.soup.find_all("link", attrs={"rel": "manifest"})

        for link_find in link_finds:
            if link_find and link_find.has_attr("href"):
                manifest_path = link_find["href"]

                return manifest_path


class XmlPage(ContentInterface):
    def __init__(self, url, contents):
        super().__init__(url=url, contents=contents)

    def is_valid(self):
        """
        This is a simple set of rules in which we reject the page:
         - status code
         - if valid HTML code
        """
        if not self.is_contents_xml():
            return False

        return True

    def is_contents_xml(self):
        if not self.get_contents():
            return False

        contents = self.get_contents()

        lower = contents.lower()
        if lower.find("<?xml") >= 0:
            return lower.find("<?xml") >= 0


class RequestsPage(object):
    def __init__(self, url, headers, timeout_s=10, ping=False):
        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """
        self.url = url
        self.response = None

        WebLogger.debug("Requests GET:{}".format(url))

        """
        stream argument allows us to read header before we fetch the page.
        SSL verification makes everything to work slower.
        """

        try:
            request_result = self.build_requests(url, headers, timeout_s)

            self.response = PageResponseObject(
                url=url,
                contents="",
                status_code=request_result.status_code,
                headers=request_result.headers,
            )

            if not self.response.is_valid():
                return

            content_length = self.response.get_content_length()
            if content_length > PAGE_TOO_BIG_BYTES:
                self.response.status_code = status_code = HTTP_STATUS_CODE_FILE_TOO_BIG
                self.response.add_error("Page is too big")
                return

            if ping:
                return

            # TODO do we want to check also content-type?

            content_type = self.response.get_content_type()

            if not content_type or self.response.is_content_type_supported():
                """
                IF we do not know the content type, or content type is supported
                """
                encoding = self.get_encoding(request_result, self.response)
                if encoding:
                    request_result.encoding = encoding

                if self.url != request_result.url:
                    self.url = request_result.url

                self.response = PageResponseObject(
                    url=self.url,
                    contents=request_result.text,
                    status_code=request_result.status_code,
                    encoding=request_result.encoding,
                    headers=request_result.headers,
                    binary=request_result.content,
                )
            else:
                self.response.status_code = HTTP_STATUS_CODE_PAGE_UNSUPPORTE
                self.response.add_error(
                    "Page {} is not supported {}".format(self.url, content_type)
                )

        except requests.Timeout:
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_TIMEOUT
            )
            self.response.add_error("Page timeout")
        except requests.exceptions.ConnectionError:
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_CONNECTION_ERROR
            )
            self.response.add_error("Connection error")
        except Exception as E:
            WebLogger.exc(E, "Url: {}: General exception".format(self.url))

            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_EXCEPTION
            )
            self.response.add_error("General page exception")

    def get(self):
        if self.response:
            return self.response

    def get_encoding(self, request_result, response):
        """
        The default assumed content encoding for text/html is ISO-8859-1 aka Latin-1 :( See RFC-2854. UTF-8 was too young to become the default, it was born in 1993, about the same time as HTML and HTTP.
        Use .content to access the byte stream, or .text to access the decoded Unicode stream.

        chardet does not work on youtube RSS feeds.
        apparent encoding does not work on youtube RSS feeds.
        """

        url = self.url

        encoding = response.get_content_type_charset()
        if encoding:
            return encoding

        else:
            # There might be several encoding texts, if so we do not know which one to use
            if response.is_content_html():
                p = HtmlPage(url, request_result.text)
                if p.is_valid():
                    if p.get_charset():
                        return p.get_charset()
            if response.is_content_rss():
                p = RssPage(url, request_result.text)
                if p.is_valid():
                    if p.get_charset():
                        return p.get_charset()

            # TODO this might trigger download of a big file
            text = request_result.text.lower()

            if text.count("encoding") == 1 and text.find('encoding="utf-8"') >= 0:
                return "utf-8"
            elif text.count("charset") == 1 and text.find('charset="utf-8"') >= 0:
                return "utf-8"

    def build_requests(self, url, headers, timeout_s):
        """
        stream argument - will fetch page contents, when we access contents of page.
        """

        request_result = requests.get(
            url,
            headers=headers,
            timeout=timeout_s,
            verify=RequestBuilder.ssl_verify,
            stream=True,
        )

        WebLogger.info("[H] {}\n{}".format(url, request_result.headers))
        return request_result


class SeleniumDriver(object):
    def get_driver(self):
        """
        https://www.lambdatest.com/blog/internationalization-with-selenium-webdriver/

        locale="en-US"

        For chrome
        options.add_argument("--lang={}".format(locale))

        # For firefox:
        profile = webdriver.FirefoxProfile()
        profile.set_preferences("intl.accept_languages", locale)
        profile.update_preferences()
        """
        raise NotImplementedError("Provide selenium driver implementation!")

    def get_selenium_status_code(self, driver):
        status_code = 200
        try:
            logs = driver.get_log("performance")
            status_code2 = self.get_selenium_status_code_from_logs(logs)
            if status_code2:
                status_code = status_code2
        except Exception as E:
            WebLogger.exc(E, "Chrome webdrider error.")
        return status_code

    def get_selenium_status_code_from_logs(self, logs):
        """
        https://stackoverflow.com/questions/5799228/how-to-get-status-code-by-using-selenium-py-python-code
        TODO should we use selenium wire?
        """
        last_status_code = 200
        for log in logs:
            if log["message"]:
                d = json.loads(log["message"])

                content_type = ""
                try:
                    content_type = d["message"]["params"]["response"]["headers"][
                        "content-type"
                    ]
                except Exception as E:
                    pass
                try:
                    content_type = d["message"]["params"]["response"]["headers"][
                        "Content-Type"
                    ]
                except Exception as E:
                    pass

                try:
                    response_received = (
                        d["message"]["method"] == "Network.responseReceived"
                    )
                    if content_type.find("text/html") >= 0 and response_received:
                        last_status_code = d["message"]["params"]["response"]["status"]
                except Exception as E:
                    # we expect that some contents do not have this
                    pass

        return last_status_code

    def get_selenium_headers(self, driver):
        headers = {}
        try:
            logs = driver.get_log("performance")
            headers = self.get_selenium_headers_logs(logs)
            return headers
        except Exception as E:
            WebLogger.exc(E, "Chrome webdrider error")

        return headers

    def get_selenium_headers_logs(self, logs):
        """
        https://stackoverflow.com/questions/5799228/how-to-get-status-code-by-using-selenium-py-python-code
        TODO should we use selenium wire?
        """
        headers = {}
        for log in logs:
            if log["message"]:
                d = json.loads(log["message"])

                content_type = ""
                try:
                    headers = d["message"]["params"]["response"]["headers"]
                except Exception as E:
                    pass

        return headers


class SeleniumChromeHeadless(SeleniumDriver):
    def get_driver(self):
        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--lang={}".format("en-US"))

        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def __init__(self, url, headers, timeout_s=10, ping=False):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        self.url = url
        self.response = None

        # if not RequestBuilder.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = timeout_s + 10

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(url)
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            status_code = self.get_selenium_status_code(driver)

            headers = self.get_selenium_headers(driver)
            WebLogger.debug("Selenium headers:{}\n{}".format(url, headers))

            # if self.options.link_redirect:
            #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

            html_content = driver.page_source

            if self.url != driver.current_url:
                self.url = driver.current_url

            # TODO use selenium wire to obtain status code & headers?

            self.response = PageResponseObject(
                self.url, contents=html_content, status_code=status_code
            )
        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_TIMEOUT
            )
        except Exception as E:
            WebLogger.exc(E, "Url:{}".format(self.url))
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_EXCEPTION
            )
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response


class SeleniumChromeFull(SeleniumDriver):
    def get_driver(self):
        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--lang={}".format("en-US"))
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--remote-debugging-pipe')
        # options.add_argument('--remote-debugging-port=9222')
        # options.add_argument('--user-data-dir=~/.config/google-chrome')

        # options to enable performance log, to read status code
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # if not RequestBuilder.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        return webdriver.Chrome(service=service, options=options)

    def __init__(self, url, headers, timeout_s, ping=False):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
        """
        self.url = url
        self.response = None

        import os

        os.environ["DISPLAY"] = ":10.0"

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = timeout_s + 20

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(url)

            status_code = self.get_selenium_status_code(driver)

            # This driver wait resulted in timeout on yahoo
            # if self.options.link_redirect:
            # WebDriverWait(driver, selenium_timeout).until(
            #    EC.url_changes(driver.current_url)
            # )
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = driver.page_source

            if self.url != driver.current_url:
                self.url = driver.current_url

            self.response = PageResponseObject(
                self.url, contents=page_source, status_code=status_code
            )

        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_TIMEOUT
            )
        except Exception as E:
            WebLogger.exc(E, "Url:{}".format(self.url))
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_EXCEPTION
            )
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response


class SeleniumUndetected(object):
    def get_driver(self):
        import undetected_chromedriver as uc

        service = Service(executable_path="/usr/bin/chromedriver")

        options = uc.ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_argument("--lang={}".format("en-US"))

        return uc.Chrome(service=service, options=options)

    def __init__(self, url, headers, timeout_s=10, ping=False):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        This does not work on raspberry pi
        """
        self.url = url
        self.response = None

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = timeout_s + 20

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(url)

            status_code = self.get_selenium_status_code(driver)

            # This driver wait resulted in timeout on yahoo
            # if self.options.link_redirect:
            # WebDriverWait(driver, selenium_timeout).until(
            #    EC.url_changes(driver.current_url)
            # )
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = driver.page_source

            if self.url != driver.current_url:
                self.url = driver.current_url

            self.response = PageResponseObject(
                self.url, contents=page_source, status_code=status_code
            )

        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(
                self.url, contents=None, status_code=HTTP_STATUS_CODE_TIMEOUT
            )
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response


class PageOptions(object):
    """
    Options object, configuration
    """

    def __init__(self):
        self.use_full_browser = False
        self.use_headless_browser = False
        self.ssl_verify = False
        self.fast_parsing = True
        self.custom_user_agent = ""
        self.link_redirect = False

    def use_basic_crawler(self):
        return not self.is_advanced_processing_required()

    def is_advanced_processing_required(self):
        return self.use_full_browser or self.use_headless_browser

    def __str__(self):
        return "F:{} H:{} SSL:{} R:{}".format(
            self.use_full_browser,
            self.use_headless_browser,
            self.ssl_verify,
            self.link_redirect,
        )

    def get_str(self):
        return str(self)


class PageResponseObject(object):
    STATUS_CODE_OK = 200
    STATUS_CODE_ERROR = 500
    STATUS_CODE_UNDEF = 0

    def __init__(
        self,
        url,
        contents=None,
        status_code=STATUS_CODE_OK,
        encoding=None,
        headers=None,
        binary=None,
    ):
        """
        @param contents Text

        TODO this should be cleaned up. We should pass binary, and encoding
        """
        self.errors = []
        self.url = url
        self.status_code = status_code

        self.content = contents
        # decoded contents
        self.text = contents
        self.binary = binary

        # I read selenium always assume utf8 encoding

        # encoding = chardet.detect(contents)['encoding']
        # self.apparent_encoding = encoding
        # self.encoding = encoding

        if not headers:
            self.headers = {}
        else:
            self.headers = headers

        if not self.is_headers_empty():
            charset = self.get_content_type_charset()
            if charset:
                self.encoding = charset
                self.apparent_encoding = charset
            elif encoding:
                self.encoding = encoding
                self.apparent_encoding = encoding
            else:
                self.encoding = "utf-8"
                self.apparent_encoding = "utf-8"
        else:
            self.encoding = encoding
            self.apparent_encoding = encoding

    def is_headers_empty(self):
        return len(self.headers) == 0

    def get_content_type(self):
        if "Content-Type" in self.headers:
            return self.headers["Content-Type"]
        if "content-type" in self.headers:
            return self.headers["content-type"]

    def get_headers(self):
        return self.headers

    def get_last_modified(self):
        date = None
        if "Last-Modified" in self.headers:
            date = self.headers["Last-Modified"]
        if "last-modified" in self.headers:
            date = self.headers["last-modified"]

    def get_content_type_charset(self):
        content = self.get_content_type()
        if not content:
            return

        elements = content.split(";")
        for element in elements:
            wh = element.lower().find("charset")
            if wh >= 0:
                charset_elements = element.split("=")
                if len(charset_elements) > 1:
                    charset = charset_elements[1]

                    if charset.startswith('"') or charset.startswith("'"):
                        return charset[1:-1]
                    else:
                        return charset

    def is_content_html(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("html") >= 0:
            return True

    def is_content_image(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("image") >= 0:
            return True

    def is_content_rss(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("rss") >= 0:
            return True
        if content.lower().find("xml") >= 0:
            return True

    def get_content_length(self):
        if "content-length" in self.headers:
            return int(self.headers["content-length"])
        if "Content-Length" in self.headers:
            return int(self.headers["Content-Length"])

        return 100

    def is_content_type_supported(self):
        """
        You can preview on a browser headers. Ctr-shift-i on ff
        """
        content_type = self.get_content_type()
        if content_type.find("text") >= 0:
            return True
        if content_type.find("application") >= 0:
            return True
        if content_type.find("xml") >= 0:
            return True

        return False

    def get_redirect_url(self):
        if (
            self.is_this_status_redirect()
            and "Location" in self.headers
            and self.headers["Location"]
        ):
            return self.headers["Location"]

    def is_this_status_ok(self):
        if self.status_code == 0:
            return False

        return self.status_code >= 200 and self.status_code < 300

    def is_this_status_redirect(self):
        """
        HTML code 403 - some pages block you because of your user agent. This code says exactly that.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
        """
        return (
            self.status_code > 300 and self.status_code < 400
        ) or self.status_code == 403

    def is_this_status_nok(self):
        """
        This function informs that status code is so bad, that further communication does not make any sense
        """
        if self.is_this_status_redirect():
            return False

        return self.status_code < 200 or self.status_code >= 400

    def is_valid(self):
        if self.is_this_status_nok():
            return False

        return True

    def get_status_code(self):
        return self.status_code

    def get_contents(self):
        return self.content

    def get_binary(self):
        return self.binary

    def add_error(self, error_text):
        self.errors.append(error_text)

    def to_bytes(self):
        # send first known data. terminated by 0 byte
        # url | status_code | headers | contents |

        # TODO this cannot be send as json, as there are many things that can be in page contents
        b1 = self.string_to_bytes("url", self.url)
        b2 = self.string_to_bytes("status_code", str(self.status_code))

        headers = json.dumps(self.headers)

        b3 = self.string_to_bytes("headers", headers)
        b4 = self.string_to_bytes("page_content", self.content)

        b1.extend(b2)
        b1.extend(b3)
        b1.extend(b4)
        return b1

    def command_to_bytes(self, command_string, bytes):
        command_string = command_string + ":"

        total = bytearray(command_string.encode())
        total.extend(bytearray(bytes))
        total.extend(bytearray((0).to_bytes(1, byteorder="big")))
        return total

    def string_to_bytes(self, command_string, string):
        if string is None:
            return self.command_to_bytes(command_string, "None".encode())
        else:
            return self.command_to_bytes(command_string, string.encode())

    def from_bytes(self, read_message):
        read_message = bytearray(read_message)

        index = 0
        while True:
            command, data, read_message = self.get_command_list(read_message)
            if not command:
                break

            if command == "url":
                self.url = data.decode()

            if command == "status_code":
                try:
                    self.status_code = int(data.decode())
                except Exception as E:
                    print("Error {}".format(E))

            if command == "headers":
                try:
                    self.headers = json.loads(data.decode())
                except Exception as E:
                    print("Error {}".format(E))

            if command == "page_content":
                self.content = data.decode()

    def get_command_bytes(self, read_message):
        wh = read_message.find(b"\x00")

        if wh >= 0:
            command = read_message[:wh]
            read_message = read_message[wh + 1 :]

            return [command, read_message]

        return [None, None]

    def get_command_list(self, read_message):
        command, remaining = self.get_command_bytes(read_message)

        if not command:
            return [None, None, None]

        wh = command.find(b"\x3A")
        if not wh:
            print("Cannot find ':' in response")
            return [None, None, None]

        else:
            command_string = command[:wh].decode()
            data = command[wh + 1 :]
            return [command_string, data, remaining]


class RequestBuilder(object):
    """
    Should not contain any HTML/RSS content processing.
    This should be just a builder.

    TODO rename HttpRequest
    """

    # use headers from https://www.supermonitoring.com/blog/check-browser-http-headers/
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
    get_contents_function = None
    ssl_verify = True
    crawling_headless_script = None
    crawling_full_script = None

    def __init__(self, url=None, response=None, options=None, page_object=None):
        """
        @param url URL
        @param contents URL page contents
        @param use_selenium decides if selenium is used
        @param page_object All settings are used from page object, with page contents
        """
        self.response = None

        if page_object:
            self.url = page_object.url
            self.options = page_object.options
            self.dead = page_object.dead
            self.response = page_object.response
            self.robots_contents = page_object.robots_contents
        else:
            self.url = url
            self.options = options
            self.robots_contents = None
            self.response = response

            # Flag to not retry same contents requests for things we already know are dead
            self.dead = False

        if self.url is None:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            WebLogger.error("Passed incorrect url {}".format(stack_str))
            return

        if self.url.lower().find("https") >= 0:
            self.protocol = "https"
        elif self.url.lower().find("http") >= 0:
            self.protocol = "http"
        else:
            self.protocol = "https"

        if not self.options:
            self.options = PageOptions()

        if RequestBuilder.get_contents_function is None:
            self.get_contents_function = self.get_contents_internal

        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Charset": "utf-8,ISO-8859-1;q=0.7,*;q=0.3",
            "Accept-Encoding": "none",
            "Accept-Language": "en-US,en;q=0.8",
            "Connection": "keep-alive",
        }

    def disable_ssl_warnings():
        RequestBuilder.ssl_verify = False
        disable_warnings(InsecureRequestWarning)

    def get_response(self):
        if self.response:
            return self.response

        if self.dead:
            return None

        self.get_response_implementation()

        return self.response

    def get_contents(self):
        response = self.get_response()
        if response:
            return response.get_contents()

    def get_binary(self):
        response = self.get_response()
        if response:
            return response.get_binary()

    def get_contents_internal(self, url, headers, timeout_s, ping=False):
        if self.options.use_basic_crawler():
            return self.get_contents_via_requests(
                self.url, headers=headers, timeout_s=timeout_s, ping=ping
            )
        elif self.options.use_headless_browser:
            if RequestBuilder.crawling_headless_script:
                return self.get_contents_via_script_headless(
                    self.url, headers=headers, timeout_s=timeout_s, ping=ping
                )
            if selenium_feataure_enabled:
                return self.get_contents_via_selenium_chrome_headless(
                    self.url, headers=headers, timeout_s=timeout_s, ping=ping
                )

            return self.get_contents_via_requests(
                self.url, headers=headers, timeout_s=timeout_s, ping=ping
            )
        elif self.options.use_full_browser:
            if RequestBuilder.crawling_full_script:
                return self.get_contents_via_script_full(
                    self.url, headers=headers, timeout_s=timeout_s, ping=ping
                )
            if selenium_feataure_enabled:
                return self.get_contents_via_selenium_chrome_full(
                    self.url, headers=headers, timeout_s=timeout_s, ping=ping
                )

            return self.get_contents_via_requests(
                self.url, headers=headers, timeout_s=timeout_s, ping=ping
            )
        else:
            self.dead = True
            raise NotImplementedError("Could not identify method of page capture")

    def get_contents_via_requests(self, url, headers, timeout_s, ping):
        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """

        p = RequestsPage(url, headers=headers, timeout_s=timeout_s, ping=ping)
        return p.get()

    def get_contents_via_selenium_chrome_headless(self, url, headers, timeout_s, ping):
        p = SeleniumChromeHeadless(url, headers=headers, timeout_s=timeout_s, ping=ping)
        return p.get()

    def get_contents_via_selenium_chrome_full(self, url, headers, timeout_s, ping):
        p = SeleniumChromeFull(url, headers=headers, timeout_s=timeout_s, ping=ping)
        return p.get()

    def get_contents_via_script_headless(self, url, headers, timeout_s, ping):
        script = RequestBuilder.crawling_headless_script

        return self.get_contents_via_script(script, url, headers, timeout_s, ping)

    def get_contents_via_script_full(self, url, headers, timeout_s, ping):
        script = RequestBuilder.crawling_full_script

        return self.get_contents_via_script(script, url, headers, timeout_s, ping)

    def get_contents_via_script(self, script, url, headers, timeout_s, ping):
        """
        TODO There might be collision if apache and celery called same script at the same time.
        """
        import os
        from pathlib import Path

        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)

        operating_path = full_path.parents[1]
        response_file_location = full_path.parents[0] / "response.txt"

        script = script.replace("$URL", url)
        script = script.replace("$RESPONSE_FILE", str(response_file_location))

        if response_file_location.exists():
            response_file_location.unlink()

        # WebLogger.debug(operating_path)
        # WebLogger.debug(response_file_location)

        p = subprocess.run(script, shell=True, capture_output=True, cwd=operating_path)

        if p.stdout:
            stdout_str = p.stdout.decode()
            WebLogger.debug(stdout_str)

        if response_file_location.exists():
            with open(str(response_file_location), "rb") as fh:
                all_bytes = fh.read()
                o = PageResponseObject(url)
                o.from_bytes(all_bytes)

                return o
        else:
            if p.stderr:
                stderr_str = p.stderr.decode()
                if stderr_str and stderr_str != "":
                    WebLogger.error("Url:{}. {}".format(url, stderr_str))

            return PageResponseObject( self.url, contents=None, status_code=HTTP_STATUS_CODE_EXCEPTION)

    def ping(self, timeout_s=5):
        url = self.url

        if url is None:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            WebLogger.error("Passed incorrect url {}".format(stack_str))
            return

        try:
            response = self.get_contents_function(
                url=url,
                headers=self.headers,
                timeout_s=timeout_s,
                ping=True,
            )

            return response is not None and response.is_valid()

        except Exception as E:
            WebLogger.exc(E, "Url:{}. Ping error\n".format(self.url))
            return False

    def get_headers_response(self, timeout_s=5):
        url = self.url

        if url is None:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            WebLogger.error("Passed incorrect url {}".format(stack_str))
            return

        try:
            response = self.get_contents_function(
                url=url,
                headers=self.headers,
                timeout_s=timeout_s,
                ping=True,
            )
            if response and response.is_valid():
                return response

        except Exception as E:
            WebLogger.exc(E, "Url:{}. Header request error\n".format(self.url))
            return None

    def get_response_implementation(self):
        if self.response and self.response.contents:
            return self.response

        if not self.user_agent or self.user_agent == "":
            self.dead = True
            return None

        if self.dead:
            return None

        if not self.is_url_valid():
            lines = traceback.format_stack()
            line_text = ""
            for line in lines:
                line_text += line

            WebLogger.error(
                "Url: Url is invalid{};Lines:{}".format(self.url, line_text)
            )

            self.dead = True
            return None

        try:
            WebLogger.debug(
                "Url: Requesting page: {} options:{}".format(self.url, self.options)
            )

            self.response = self.get_contents_function(
                self.url, headers=self.headers, timeout_s=10
            )

            WebLogger.debug(
                "Url: Requesting page: {} DONE".format(self.url, self.options)
            )

        except Exception as E:
            self.dead = True
            WebLogger.exc(E, "Url:{}".format(self.url))

        return self.response

    @lazy_load_content
    def is_valid(self):
        if not self.response:
            return False

        if self.response.is_this_status_ok() or self.response.is_this_status_redirect():
            return True
        else:
            return False

    def is_url_valid(self):
        if self.url == None:
            return False

        p = DomainAwarePage(self.url)
        if not p.is_web_link():
            return False

        return True

    def try_decode(self, thebytes):
        try:
            return thebytes.decode("UTF-8", errors="replace")
        except Exception as e:
            pass

    def is_this_status_ok(self, status_code):
        if status_code == 0:
            return False

        return status_code >= 200 and status_code < 300


class InternetPageHandler(ContentInterface):
    def __init__(self, url=None, page_options=None):
        super().__init__(url=url, contents=None)

        self.p = None  # page contents object, HtmlPage, RssPage, or whathver
        self.response = None
        self.options = page_options
        self.browser_promotions = True

    def get_contents(self):
        if self.response and self.response.get_contents():
            return self.response.get_contents()

        return self.get_contents_implementation()

    def get_contents_implementation(self):
        self.p = self.get_page_handler_simple()

        if self.browser_promotions and self.is_advanced_processing_possible():
            # we warn, because if that happens too often, it is easy just to
            # define EntryRule for that domain
            WebLogger.error(
                "Url:{}. Trying to workaround with headless browser".format(self.url)
            )
            self.options.use_headless_browser = True
            self.p = self.get_page_handler_simple()

        if self.response:
            return self.response.get_contents()

    def get_page_handler_simple(self):
        url = self.url

        dap = DomainAwarePage(url)

        if url.startswith("https") or url.startswith("http"):
            if not dap.is_media():
                p = RequestBuilder(url=url, options=self.options)
                self.response = p.get_response()
                contents = p.get_contents()

                if not p.is_valid():
                    return

        else:
            # Other protocols have not been yet implemented
            # there is no request, there is no response
            pass

        if contents:
            """
            Found servers that return content-type "text/html" for RSS sources :(
            """

            if self.is_html():
                p = HtmlPage(url, contents)
                return p

            if self.is_rss():
                p = RssPage(url, contents)
                return p

            # we do not know what it is. Guess

            p = HtmlPage(url, contents)
            if p.is_valid():
                return p

            p = RssPage(url, contents)
            if p.is_valid():
                return p

            p = JsonPage(url, contents)
            if p.is_valid():
                return p

            # TODO
            # p = XmlPage(url, contents)
            # if p.is_valid():
            #    return p

            p = DefaultContentPage(url, contents)
            return p

        if self.response and self.response.is_valid():
            p = DefaultContentPage(url, contents)
            return p

    def is_advanced_processing_possible(self):
        """
        If we do not have data, but we think we can do better
        """
        if not self.response:
            return True

        status_code = self.response.get_status_code()
        if status_code == HTTP_STATUS_CODE_CONNECTION_ERROR:
            return False

        if status_code < 200 or status_code > 404:
            if self.options.use_basic_crawler():
                return True
            else:
                return False

        if not self.options.use_basic_crawler():
            return False

        if not self.p:
            return True

        if self.p and self.p.is_cloudflare_protected():
            return True

        if not self.p.is_valid():
            # if we have response, but it is invalid, we may try obtaining contents with more advanced processing
            return True

        if self.get_contents() == "" or self.get_contents() is None:
            return True

        return False

    def is_status_code_redirect(self, status_code):
        return (status_code >= 300 and status_code < 400) or status_code == 403

    def is_html(self):
        if (
            self.response
            and self.response.get_content_type() is not None
            and self.response.is_content_html()
        ):
            return True

    def is_rss(self):
        if (
            self.response
            and self.response.get_content_type() is not None
            and self.response.is_content_rss()
        ):
            return True

    def get_title(self):
        if not self.p:
            return
        return self.p.get_title()

    def get_description(self):
        if not self.p:
            return
        return self.p.get_description()

    def get_language(self):
        if not self.p:
            return
        return self.p.get_language()

    def get_thumbnail(self):
        if not self.p:
            return
        return self.p.get_thumbnail()

    def get_author(self):
        if not self.p:
            return
        return self.p.get_author()

    def get_album(self):
        if not self.p:
            return
        return self.p.get_album()

    def get_tags(self):
        if not self.p:
            return
        return self.p.get_tags()

    def get_date_published(self):
        if not self.p:
            return
        return self.p.get_date_published()

    def get_properties(self):
        if not self.p:
            return

        props = self.p.get_properties()
        props["status_code"] = self.response.status_code
        return props

    def get_page_rating_vector(self):
        result = []
        if not self.p:
            return result

        """
        TODO include this somehow
        """
        if self.response:
            result.append(self.get_page_rating_status_code(self.response.status_code))

        result.extend(self.p.get_page_rating_vector())
        return result

    def get_page_rating_status_code(self, status_code):
        rating = 0
        if status_code == 200:
            rating += 10
        elif status_code >= 200 and status_code <= 300:
            rating += 5
        elif status_code != 0:
            rating += 1

        return [rating, 10]

    def get_status_code(self):
        if not self.response:
            return PageResponseObject.STATUS_CODE_UNDEF

        return self.response.status_code

    def is_valid(self):
        if not self.p:
            return False

        # not valid HTTP response
        response = self.response
        if not response or not response.is_valid():
            return False

        return self.p.is_valid()

    def is_cloudflare_protected(self):
        if not self.p:
            return False

        return self.p.is_cloudflare_protected()

    def get_response(self):
        if self.response:
            return self.response

        self.get_contents_implementation()

        if self.response:
            return self.response

    def get_favicon(self):
        if self.p:
            if type(self.p) is HtmlPage:
                favs = self.p.get_favicons()
                if favs and len(favs) > 0:
                    return list(favs.keys())[0]


class Url(ContentInterface):
    """
    Encapsulates data page, and builder to make request
    """

    def __init__(self, url=None, page_object=None, page_options=None):
        if page_object:
            self.url = page_object.url
        else:
            self.url = url

        self.options = self.get_init_page_options(page_options)

        self.handler = None
        self.response = None
        self.contents = None

    def get_init_page_options(self, initial_options=None):
        options = PageOptions()

        if initial_options and initial_options.use_headless_browser:
            options.use_headless_browser = initial_options.use_headless_browser
        if initial_options and initial_options.use_full_browser:
            options.use_full_browser = initial_options.use_full_browser

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

        self.handler = self.get_handler_implementation()
        if self.handler:
            self.response = self.handler.get_response()
            self.contents = self.handler.get_contents()

            return self.response

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
        """
        # based on link 'appearance'

        page_type = DomainAwarePage(url).get_type()

        if page_type == URL_TYPE_HTML:
            return HtmlPage(url, "")

        if page_type == URL_TYPE_RSS:
            return RssPage(url, "")

    def get_handler_implementation(self):
        contents = None
        url = self.url

        if url.startswith("https") or url.startswith("http"):
            return InternetPageHandler(url, page_options=self.options)
        elif url.startswith("smb") or url.startswith("ftp"):
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
        p = RequestBuilder(robots_url)
        self.robots_contents = p.get_contents()

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
            p = RequestBuilder(url=url)
            contents = p.get_contents()
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

        b = RequestBuilder(site)
        contents = b.get_contents()

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
