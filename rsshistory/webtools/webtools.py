"""
This file should not include any other or django related files.

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
    - PageRequestObject - request
    - PageResponseObject - page response, interface for all implementations
"""

import hashlib
import html
import traceback
import re
import json
from dateutil import parser
import urllib.request, urllib.error, urllib.parse
from bs4 import BeautifulSoup

from utils.dateutils import DateUtils

__version__ = "0.0.5"


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
    """
    Logging interface
    """

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
            or self.url.startswith("\\\\")
        ):
            # https://mailto is not a good link
            if self.url.find(".") == -1:
                return False

            return True

        return False

    def is_protocolled_link(self):
        if (
            self.url.startswith("http://")
            or self.url.startswith("https://")
            or self.url.startswith("smb://")
            or self.url.startswith("ftp://")
            or self.url.startswith("//")
            or self.url.startswith("\\\\")
        ):
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

    def get_port(self):
        parts = self.parse_url()

        if not parts:
            return

        if len(parts) > 1:
            wh = parts[2].find(":")
            if wh == -1:
                return
            else:
                try:
                    port = int(parts[2][wh + 1 :])
                    return port
                except ValueError as E:
                    return

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
                args = self.parse_argument(rest_data[1])
                if args[1] != "":
                    return [protocol, "://", rest_data[0], args[0], args[1]]
                else:
                    return [protocol, "://", rest_data[0], rest_data[1]]
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
                args = self.parse_argument(rest_data[1])
                if args[1] != "":
                    return ["", separator, rest_data[0], args[0], args[1]]
                else:
                    return ["", separator, rest_data[0], rest_data[1]]
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
        if self.url and not x.is_protocolled_link():
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
            # protocol + sep + domain
            result.extend(parts[0:3])

        if len(parts) > 3:
            for part in parts[3:]:
                if part.startswith("\\"):
                    part = part[1:]
                if part.startswith("/"):
                    part = part[1:]
                if part.endswith("\\"):
                    part = part[:-1]
                if part.endswith("/"):
                    part = part[:-1]

                if part.find("\\") >= 0:
                    result.extend(part.split("\\"))
                elif part.find("/") >= 0:
                    result.extend(part.split("/"))
                else:
                    result.append(part)

        return result

    def join(self, parts):
        result = ""

        result = parts[0] + parts[1] + parts[2]

        for part in parts[3:]:
            if result.endswith("/"):
                result = result[:-1]
            if result.endswith("\\"):
                result = result[:-1]

            if part.startswith("/"):
                part = part[1:]
            if part.startswith("\\"):
                part = part[1:]

            if part.endswith("/"):
                part = part[:-1]
            if part.endswith("\\"):
                part = part[:-1]

            if part.startswith("?") or part.startswith("#"):
                result = result + part
            else:
                result = result + "/" + part

        return result


class PageOptions(object):
    """
    Page request options. Serves more like request API.

    API user defines if headless browser is required.
    WebTools can be configured to use a script, port, or whatever

    Fields:
     - ping - only check status code, and headers of page. Does not download contents
     - browser promotions - if requests cannot receive response we can try with headless or full browser
     - user_agent - not supported by all crawlers. Selenium, stealth requests uses their own agents
     - mode_mapping - configuration of modes
    """

    def __init__(self):
        self.ssl_verify = True
        self.ping = False
        self.use_browser_promotions = (
            True  # tries headles if normal processing does not work
        )

        self.mode_mapping = {}

        self.user_agent = None  # passed if you wish certain user agent to be used

    def is_mode_mapping(self):
        if self.mode_mapping and len(self.mode_mapping) > 0:
            return True

    def copy_config(self, other_config):
        # if we have mode mapping - use it
        self.mode_mapping = other_config.mode_mapping
        self.ssl_verify = other_config.ssl_verify

    def __str__(self):
        if self.mode_mapping and len(self.mode_mapping) > 0:
            return "Browser:{} P:{} SSL:{} PR:{}".format(
                self.mode_mapping[0],
                self.ping,
                self.ssl_verify,
                self.use_browser_promotions,
            )
        else:
            return "Browser:None P:{} SSL:{} PR:{}".format(
                self.ping,
                self.ssl_verify,
                self.use_browser_promotions,
            )

    def get_str(self):
        return str(self)

    def get_crawler(self, name):
        for mode_data in self.mode_mapping:
            if "enabled" in mode_data:
                if mode_data["name"] == name and mode_data["enabled"] == True:
                    return mode_data
            else:
                if mode_data["name"] == name:
                    return mode_data

    def bring_to_front(self, input_data):
        result = [input_data]
        for mode_data in self.mode_mapping:
            if mode_data == input_data:
                continue

            result.append(mode_data)

        self.mode_mapping = result

    def get_timeout(self, timeout_s):
        if not self.mode_mapping or len(self.mode_mapping) == 0:
            return timeout_s

        first_mode = self.mode_mapping[0] 

        if "settings" not in first_mode:
            return timeout_s

        settings = first_mode["settings"]

        if "timeout" in settings:
            timeout_crawler = settings["timeout"]
            return timeout_crawler

        return timeout_s


class PageRequestObject(object):
    """
    Precise information for scraping.
    Should contain information about what is to be scraped. Means of scraping should not be apart of this.

    @example Url, timeout is OK.
    @example Scarping script name, port, is not OK
    """

    def __init__(
        self,
        url,
        headers=None,
        user_agent=None,
        timeout_s=10,
        ping=False,
        ssl_verify=True,
    ):
        self.url = url

        self.user_agent = user_agent
        if headers:
            self.headers = headers
        else:
            self.headers = None  # not set, use default

        self.timeout_s = timeout_s
        self.ping = False
        self.ssl_verify = True

    def __str__(self):
        return "Url:{} Timeout:{} Ping:{}".format(self.url, self.timeout_s, self.ping)


class PageResponseObject(object):
    STATUS_CODE_OK = 200
    STATUS_CODE_ERROR = 500
    STATUS_CODE_UNDEF = 0

    def __init__(
        self,
        url=None,  # received url
        binary=None,
        text=None,
        status_code=STATUS_CODE_OK,
        encoding=None,
        headers=None,
        request_url=None,
    ):
        """
        @param contents Text

        TODO this should be cleaned up. We should pass binary, and encoding
        """
        self.errors = []
        self.url = url
        self.request_url = request_url
        self.status_code = status_code

        self.binary = None
        self.text = None

        if binary:
            self.binary = binary
        if text:
            self.text = text

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

        if not self.encoding:
            self.encoding = "utf-8"
            self.apparent_encoding = "utf-8"

        if self.binary and not self.text:
            try:
                self.text = self.binary.decode(self.encoding)
            except Exception as E:
                WebLogger.exc(
                    E, "Cannot properly decode ansower from {}".format(self.url)
                )
                self.text = self.binary.decode(self.encoding, errors="ignore")

        if self.text and not self.binary:
            try:
                self.binary = self.text.encode(self.encoding)
            except Exception as E:
                WebLogger.exc(
                    E, "Cannot properly encode ansower from {}".format(self.url)
                )
                self.binary = self.text.encode(self.encoding, errors="ignore")

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

        if date:
            return date_str_to_date(date)

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

    def is_content_json(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("json") >= 0:
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

    def get_text(self):
        return self.text

    def get_binary(self):
        return self.content

    def set_text(self, text, encoding=None):
        if encoding:
            self.encoding = encoding
        else:
            if self.encoding is None:
                self.encoding = "utf-8"

        self.text = text
        self.content = text.encode(self.encoding)

    def set_binary(self, binary, encoding="utf-8"):
        self.content = binary
        self.text = binary.decode(encoding)

    def add_error(self, error_text):
        self.errors.append(error_text)

    def __str__(self):
        has_text_data = "Yes" if self.text else "No"
        has_binary_data = "Yes" if self.binary else "No"

        return "PageResponseObject: Url:{} Status code:{} Headers:{} Text:{} Binary:{}".format(
            self.url,
            self.status_code,
            self.headers,
            has_text_data,
            has_binary_data,
        )


def get_request_to_bytes(request, script):
    from .ipc import string_to_command

    total_bytes = bytearray()

    bytes1 = string_to_command("PageRequestObject.__init__", "OK")
    bytes2 = string_to_command("PageRequestObject.url", request.url)
    bytes3 = string_to_command("PageRequestObject.timeout", str(request.timeout_s))
    if request.user_agent != None:
        bytes4 = string_to_command(
            "PageRequestObject.user_agent", str(request.user_agent)
        )
    else:
        bytes4 = bytearray()
    if request.headers != None:
        bytes5 = string_to_command(
            "PageRequestObject.headers", json.dumps(request.headers)
        )
    else:
        bytes5 = bytearray()

    bytes6 = string_to_command("PageRequestObject.ssl_verify", str(request.ssl_verify))
    bytes7 = string_to_command("PageRequestObject.script", script)

    bytes8 = string_to_command("PageRequestObject.__del__", "OK")

    total_bytes.extend(bytes1)
    total_bytes.extend(bytes2)
    total_bytes.extend(bytes3)
    total_bytes.extend(bytes4)
    total_bytes.extend(bytes5)
    total_bytes.extend(bytes6)
    total_bytes.extend(bytes7)
    total_bytes.extend(bytes8)

    return total_bytes


def get_response_to_bytes(response):
    from .ipc import string_to_command

    total_bytes = bytearray()

    bytes1 = string_to_command("PageResponseObject.__init__", "OK")
    bytes2 = string_to_command("PageResponseObject.url", response.url)
    bytes3 = string_to_command(
        "PageResponseObject.status_code", str(response.status_code)
    )
    if response.headers != None:
        bytes4 = string_to_command(
            "PageResponseObject.headers", json.dumps(response.headers)
        )
    else:
        bytes4 = bytearray()

    if response.text:
        bytes5 = string_to_command("PageResponseObject.text", response.text)
    elif response.binary:
        bytes5 = bytes_to_command("PageResponseObject.text", response.binary)
    else:
        bytes5 = bytearray()
    bytes6 = string_to_command(
        "PageResponseObject.request_url", str(response.request_url)
    )
    bytes7 = string_to_command("PageResponseObject.__del__", "OK")

    total_bytes.extend(bytes1)
    total_bytes.extend(bytes2)
    total_bytes.extend(bytes3)
    total_bytes.extend(bytes4)
    total_bytes.extend(bytes5)
    total_bytes.extend(bytes6)
    total_bytes.extend(bytes7)

    return total_bytes


def get_response_from_bytes(all_bytes):
    from .ipc import commands_from_bytes

    response = PageResponseObject("")

    commands_data = commands_from_bytes(all_bytes)
    for command_data in commands_data:
        if command_data[0] == "PageResponseObject.__init__":
            pass
        elif command_data[0] == "PageResponseObject.url":
            response.url = command_data[1].decode()
        elif command_data[0] == "PageResponseObject.request_url":
            response.request_url = command_data[1].decode()
        elif command_data[0] == "PageResponseObject.headers":
            try:
                response.headers = json.loads(command_data[1].decode())
            except ValueError as E:
                WebLogger.exc(E, "Exception when loading headers")
        elif command_data[0] == "PageResponseObject.status_code":
            try:
                response.status_code = int(command_data[1])
            except ValueError as E:
                WebLogger.exc(E, "Exception when loading headers")
        elif command_data[0] == "PageResponseObject.text":
            response.set_text(command_data[1].decode())
        elif command_data[0] == "PageResponseObject.__del__":
            pass

    return response


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
