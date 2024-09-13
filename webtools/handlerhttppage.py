import subprocess
import json
import os
from pathlib import Path

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from datetime import timedelta

from utils.dateutils import DateUtils
from utils.basictypes import fix_path_for_os

from .webtools import (
    WebLogger,
    WebConfig,
    PageRequestObject,
    PageResponseObject,
    PageOptions,
    DomainAwarePage,
    lazy_load_content,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_CONNECTION_ERROR,
    HTTP_STATUS_CODE_TIMEOUT,
    HTTP_STATUS_CODE_FILE_TOO_BIG,
    HTTP_STATUS_CODE_PAGE_UNSUPPORTED,
)
from .pages import (
    ContentInterface,
    DefaultContentPage,
    JsonPage,
    HtmlPage,
    RssPage,
)
from .crawlers import (
    selenium_feataure_enabled,
    RequestsCrawler,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ScriptCrawler,
    ServerCrawler,
)


class HeadlessScriptCrawler(ScriptCrawler):
    def __init__(self, request, response_file=None, response_port=None):
        self.script = self.get_script()

        if not self.script:
            return

        self.process_input()

        if self.is_valid():
            super().__init__(request=request, response_file=self.response_file, response_port=response_port, cwd=self.operating_path, script=self.script)

    def get_script(self):
        return WebConfig.crawling_headless_script

    def process_input(self):
        self.operating_path = self.get_operating_dir()
        self.response_file = self.get_response_file_name(operating_path)

    def is_valid(self):
        if not self.is_full_script_valid():
            return False

        return True

    def is_full_script_valid(self):
        full_script = self.operating_path / self.script
        if not full_script.exists():
            WebLogger.error("Script to call does not exist: {}".format(full_script))
            return

        return True

    def get_response_file_name(self, operating_path):
        file_name_url_part = fix_path_for_os(request.url)
        file_name_url_part = file_name_url_part.replace("\\", "")
        file_name_url_part = file_name_url_part.replace("/", "")
        file_name_url_part = file_name_url_part.replace("@", "")

        if WebConfig.script_responses_directory is not None:
            response_dir = Path(WebConfig.script_responses_directory)

        response_file = response_dir / "response_{}.txt".format(file_name_url_part)
        return response_file

    def get_operating_dir(self):

        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)

        if WebConfig.script_operating_dir is None:
            operating_path = full_path.parents[1]
        else:
            operating_path = Path(WebConfig.script_operating_dir)

        if not operating_path.exists():
            WebLogger.error("Operating path does not exist: {}".format(operating_path))
            return

        return operating_path


class FullScriptCrawler(ScriptCrawler):
    def __init__(self, request, response_file=None, response_port=None):
        super().__init__(self, request, response_file, response_port)

    def get_script(self):
        return WebConfig.crawling_full_script


class HeadlessServerCrawler(ServerCrawler):
    def __init__(self, request, response_file=None, response_port=None):
        script = self.get_script()

        port = self.get_port()
        super().__init__(request=request, response_file=response_file, response_port=port, script=script)

    def get_script(self):
        if not WebConfig.crawling_server_port:
            return

        script = WebConfig.crawling_headless_script
        if script is None:
            script = "poetry run python crawleebeautifulsoup.py"

        return script

    def get_port(self):
        port = WebConfig.crawling_server_port


class FullServerCrawler(ServerCrawler):
    def __init__(self, request, response_file=None, response_port=None):
        script = self.get_script()

        port = self.get_port()
        super().__init__(request=request, response_file=response_file, response_port=port, script=script)

    def get_script(self):
        if not WebConfig.crawling_server_port:
            return

        script = WebConfig.crawling_full_script
        if script is None:
            script = "poetry run python crawleeplaywright.py"

        return script

    def get_port(self):
        port = WebConfig.crawling_server_port


class ConfiguredSeleniumChromeHeadless(SeleniumChromeHeadless):
    def __init__(self, request, response_file=None, response_port=None, driver_executable = None):
        driver_executable=WebConfig.selenium_driver_location
        super().__init__(request, response_file=response_file, response_port=response_port, driver_executable = driver_executable)


class ConfiguredSeleniumChromeFull(SeleniumChromeFull):
    def __init__(self, request, response_file=None, response_port=None, driver_executable = None):
        driver_executable=WebConfig.selenium_driver_location
        super().__init__(request, response_file=response_file, response_port=response_port, driver_executable = driver_executable)


class HttpRequestBuilder(object):
    """
    Should not contain any HTML/RSS content processing.
    This should be just a builder.

    It should not be called directly, nor used
    """

    # use headers from https://www.supermonitoring.com/blog/check-browser-http-headers/
    get_contents_function = None

    def __init__(self, url=None, options=None, page_object=None, request=None):
        """
        @param url URL
        @param contents URL page contents
        @param use_selenium decides if selenium is used
        @param page_object All settings are used from page object, with page contents
        """
        self.request = request
        self.response = None
        self.timeout_s = 10

        if page_object:
            self.url = page_object.url
            self.options = page_object.options
            self.dead = page_object.dead
            self.robots_contents = page_object.robots_contents
        else:
            self.url = url
            self.options = options
            self.robots_contents = None

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

        self.user_agent = None
        if request:
            if request.user_agent:
                self.user_agent = request.user_agent

        if not self.user_agent:
            self.user_agent = HttpPageHandler.user_agent

        if HttpRequestBuilder.get_contents_function is None:
            self.get_contents_function = self.get_contents_internal

        self.headers = None
        if request:
            if request.headers:
                self.headers = request.headers

        if not self.headers:
            self.headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Charset": "utf-8,ISO-8859-1;q=0.7,*;q=0.3",
                "Accept-Encoding": "none",
                "Accept-Language": "en-US,en;q=0.8",
                "Connection": "keep-alive",
            }

    def get_response(self):
        if self.response:
            return self.response

        if self.dead:
            return None

        self.get_response_implementation()

        return self.response

    def get_text(self):
        response = self.get_response()
        if response:
            return response.get_text()

    def get_binary(self):
        response = self.get_response()
        if response:
            return response.get_binary()

    def get_contents_internal(self, request):
        """
        There are 3 levels of scraping:
         - requests (fast)
         - if above fails we can use headless browser
         - if above fails we can use full browser (most advanced, resource consuming)

        First configured thing provides return value
        """
        request.timeout_s = max(request.timeout_s, 10)
        if self.options:
            request.ssl_verify = self.options.ssl_verify
        if self.options:
            request.ping = self.options.ping

        if self.options.use_basic_crawler():
            preference_table = [
                RequestsCrawler,
                HeadlessServerCrawler,
                HeadlessScriptCrawler,
                ConfiguredSeleniumChromeHeadless,
                FullServerCrawler,
                FullScriptCrawler,
                ConfiguredSeleniumChromeFull,
            ]

            for crawler in preference_table:
                c = crawler(request=request)
                c.run()
                response = c.get_response()
                if response:
                    return response

        elif self.options.use_headless_browser:
            request.timeout_s = max(request.timeout_s, 20)

            preference_table = [
                HeadlessServerCrawler,
                HeadlessScriptCrawler,
                ConfiguredSeleniumChromeHeadless,
                FullServerCrawler,
                FullScriptCrawler,
                ConfiguredSeleniumChromeFull,
                RequestsCrawler,
            ]

            for crawler in preference_table:
                c = crawler(request=request)
                c.run()
                response = c.get_response()
                if response:
                    return response

        elif self.options.use_full_browser:
            request.timeout_s = max(request.timeout_s, 30)

            preference_table = [
                FullServerCrawler,
                FullScriptCrawler,
                ConfiguredSeleniumChromeFull,
                HeadlessServerCrawler,
                HeadlessScriptCrawler,
                ConfiguredSeleniumChromeHeadless,
                RequestsCrawler,
            ]

            for crawler in preference_table:
                c = crawler(request=request)
                c.run()
                response = c.get_response()
                if response:
                    return response
        else:
            self.dead = True
            raise NotImplementedError("Could not identify method of page capture")

    def ping(self, timeout_s=5):
        url = self.url

        if url is None:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            WebLogger.error("Passed incorrect url {}".format(stack_str))
            return

        o = PageRequestObject(
            url=url,
            headers=self.headers,
            timeout_s=timeout_s,
            ping=True,
        )

        try:
            response = self.get_contents_function(request=o)

            return response is not None and response.is_valid()

        except Exception as E:
            WebLogger.exc(E, "Url:{}. Ping error\n".format(url))
            return False

    def get_headers_response(self, timeout_s=5):
        url = self.url

        if url is None:
            stack_lines = traceback.format_stack()
            stack_str = "".join(stack_lines)

            WebLogger.error("Passed incorrect url {}".format(stack_str))
            return

        try:
            o = PageRequestObject(
                url=url,
                headers=self.headers,
                timeout_s=timeout_s,
                ping=True,
            )

            response = self.get_contents_function(request=o)
            if response and response.is_valid():
                return response

        except Exception as E:
            WebLogger.exc(E, "Url:{}. Header request error\n".format(url))
            return None

    def get_response_implementation(self):
        if self.response and self.response.text:
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

            WebLogger.error("Url:{} is invalid. Lines:{}".format(self.url, line_text))

            self.dead = True
            return None

        try:
            WebLogger.info("[R] Url:{}. Options:{}".format(self.url, self.options))

            request = PageRequestObject(
                url=self.url,
                headers=self.headers,
                timeout_s=self.timeout_s,
            )

            self.response = self.get_contents_function(request=request)

            WebLogger.info(
                "Url:{}. Options:{} Requesting page: DONE".format(
                    self.url, self.options
                )
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


class HttpPageHandler(ContentInterface):
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
    ssl_verify = True

    def __init__(self, url=None, page_options=None):
        super().__init__(url=url, contents=None)
        self.p = None  # page contents object, HtmlPage, RssPage, or whathver
        self.response = None
        self.options = page_options

    def disable_ssl_warnings():
        HttpPageHandler.ssl_verify = False
        disable_warnings(InsecureRequestWarning)

    def is_handled_by(url):
        if url.startswith("https") or url.startswith("http"):
            return True
        return False

    def get_contents(self):
        if self.response and self.response.get_text():
            return self.response.get_text()

        return self.get_contents_implementation()

    def get_response(self):
        if self.response:
            return self.response

        self.get_contents_implementation()

        if self.response:
            return self.response

    def get_contents_implementation(self):
        self.p = self.get_page_handler_simple()

        if (
            self.options.use_browser_promotions
            and self.is_advanced_processing_possible()
        ):
            # we warn, because if that happens too often, it is easy just to
            # define EntryRule for that domain
            WebLogger.error(
                "Url:{}. Trying to workaround with headless browser".format(self.url)
            )
            self.options.use_headless_browser = True
            self.p = self.get_page_handler_simple()

        if self.response:
            return self.response.get_text()

    def get_page_handler_simple(self):
        url = self.url

        dap = DomainAwarePage(url)

        if url.startswith("https") or url.startswith("http"):
            if not dap.is_media():
                p = HttpRequestBuilder(url=url, options=self.options)
                self.response = p.get_response()
                if not self.response:
                    return

                contents = self.response.get_text()

                if not p.is_valid():
                    return

        else:
            # Other protocols have not been yet implemented
            # there is no request, there is no response
            pass

        if contents:
            """ """

            if self.is_html():
                p = HtmlPage(url, contents)
                if p.is_valid():
                    return p

                # some servers might return text/html for RSS sources
                # we verify if content type is valid

                p = RssPage(url, contents)
                if p.is_valid():
                    return p

                p = JsonPage(url, contents)
                if p.is_valid():
                    return p

            if self.is_rss():
                p = RssPage(url, contents)
                if p.is_valid():
                    return p

                p = HtmlPage(url, contents)
                if p.is_valid():
                    return p

                p = JsonPage(url, contents)
                if p.is_valid():
                    return p

            if self.is_json():
                p = JsonPage(url, contents)
                if p.is_valid():
                    return p

                p = RssPage(url, contents)
                if p.is_valid():
                    return p

                p = HtmlPage(url, contents)
                if p.is_valid():
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

        # content is defined, and it is not support
        content_type = self.response.get_content_type()
        if content_type and not self.response.is_content_type_supported():
            return False

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
            text = self.response.get_text()
            print(text)
            return True

        if not self.p.is_valid():
            # if we have response, but it is invalid, we may try obtaining contents with more advanced processing
            return True

        text = self.response.get_text()

        if text == "" or text is None:
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

    def is_json(self):
        if (
            self.response
            and self.response.get_content_type() is not None
            and self.response.is_content_json()
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

    def get_favicon(self):
        if self.p:
            if type(self.p) is HtmlPage:
                favs = self.p.get_favicons()
                if favs and len(favs) > 0:
                    return list(favs.keys())[0]

    def get_entries(self):
        if self.p:
            if type(self.p) is RssPage:
                return self.p.get_entries()

    def get_feeds(self):
        # TODO ugly import
        from .handlers import RedditChannelHandler
        result = []
        url = self.url

        h = RedditChannelHandler(url)
        if h.is_handled_by():
            feeds = h.get_feeds()
            if feeds and len(feeds) > 0:
                result.extend(feeds)

        if type(self.p) is RssPage:
            # we do not add ourselve
            pass

        if type(self.p) is HtmlPage:
            feeds = self.p.get_feeds()
            if feeds and len(feeds) > 0:
                result.extend(feeds)

        return result
