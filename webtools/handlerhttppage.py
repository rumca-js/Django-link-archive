import subprocess
import json
from pathlib import Path

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from datetime import timedelta

from utils.dateutils import DateUtils
from utils.basictypes import fix_path_for_os

from .webtools import (
    ContentInterface,
    DefaultContentPage,
    WebLogger,
    JsonPage,
    HtmlPage,
    RssPage,
    PageRequestObject,
    PageResponseObject,
    PageOptions,
    DomainAwarePage,
    lazy_load_content,
    get_request_to_bytes,
    get_response_from_bytes,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_CONNECTION_ERROR,
    HTTP_STATUS_CODE_TIMEOUT,
    HTTP_STATUS_CODE_FILE_TOO_BIG,
    HTTP_STATUS_CODE_PAGE_UNSUPPORTED,
)
from .crawlers import (
    selenium_feataure_enabled,
    RequestsPage,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
)


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
        """
        request.timeout_s = max(request.timeout_s, 10)
        if self.options:
            request.ssl_verify = self.options.ssl_verify
        if self.options:
            request.ping = self.options.ping

        if self.options.use_basic_crawler():
            preference_table = [
                    self.get_contents_via_requests,
                    self.get_contents_via_server_headless,
                    self.get_contents_via_script_headless,
                    self.get_contents_via_selenium_chrome_headless,
                    self.get_contents_via_server_full,
                    self.get_contents_via_script_full,
                    self.get_contents_via_selenium_chrome_full,
                    ]

            for function in preference_table:
                result = function(request=request)
                if result:
                    return result

        elif self.options.use_headless_browser:
            request.timeout_s = max(request.timeout_s, 20)

            preference_table = [
                self.get_contents_via_server_headless,
                self.get_contents_via_script_headless,
                self.get_contents_via_selenium_chrome_headless,
                self.get_contents_via_server_full,
                self.get_contents_via_script_full,
                self.get_contents_via_selenium_chrome_full,
                self.get_contents_via_requests,
            ]

            for function in preference_table:
                result = function(request=request)
                if result:
                    return result

        elif self.options.use_full_browser:
            request.timeout_s = max(request.timeout_s, 30)

            preference_table = [
                self.get_contents_via_server_full,
                self.get_contents_via_script_full,
                self.get_contents_via_selenium_chrome_full,
                self.get_contents_via_server_headless,
                self.get_contents_via_script_headless,
                self.get_contents_via_selenium_chrome_headless,
                self.get_contents_via_requests,
            ]

            for function in preference_table:
                result = function(request=request)
                if result:
                    return result
        else:
            self.dead = True
            raise NotImplementedError("Could not identify method of page capture")

    def get_contents_via_requests(self, request):
        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """

        p = RequestsPage(request)
        p.run()
        return p.get_response()

    def get_contents_via_selenium_chrome_headless(self, request):
        p = SeleniumChromeHeadless(request)
        p.run()
        return p.get_response()

    def get_contents_via_selenium_chrome_full(self, request):
        p = SeleniumChromeFull(request)
        p.run()
        return p.get_response()

    def get_contents_via_script_headless(self, request):
        if not HttpPageHandler.crawling_headless_script:
            return

        script = HttpPageHandler.crawling_headless_script

        return self.get_contents_via_script(script, request)

    def get_contents_via_script_full(self, request):
        if not HttpPageHandler.crawling_full_script:
            return

        script = HttpPageHandler.crawling_full_script

        return self.get_contents_via_script(script, request)

    def get_contents_via_server_headless(self, request):
        if not HttpPageHandler.crawling_server_port:
            return

        script = HttpPageHandler.crawling_headless_script
        if script is None:
            script = "poetry run python crawleebeautifulsoup.py"
        port = HttpPageHandler.crawling_server_port

        return self.get_contents_via_server(script, port, request)

    def get_contents_via_server_full(self, request):
        if not HttpPageHandler.crawling_server_port:
            return

        script = HttpPageHandler.crawling_full_script
        if script is None:
            script = "poetry run python crawleeplaywright.py"
        port = HttpPageHandler.crawling_server_port

        return self.get_contents_via_server(script, port, request)

    def get_contents_via_server(self, script, port, request):
        """
        TODO what about timeout?
        """
        from .ipc import SocketConnection

        script_time_start = DateUtils.get_datetime_now_utc()

        connection = SocketConnection()
        try:
            if not connection.connect(SocketConnection.gethostname(), port):
                WebLogger.error("Cannot connect to port{}".format(port))

                response = PageResponseObject(
                    request.url,
                    text=None,
                    status_code=HTTP_STATUS_CODE_CONNECTION_ERROR,
                    request_url=request.url,
                )
                return response
        except Exception as E:
            WebLogger.exc(E, "Cannot connect to port{}".format(port))
            return

        bytes = get_request_to_bytes(request, script)
        connection.send(bytes)

        response = PageResponseObject(request.url)
        response.status_code = HTTP_STATUS_CODE_TIMEOUT
        response.request_url = request.url

        while True:
            command_data = connection.get_command_and_data()

            if command_data:
                if command_data[0] == "PageResponseObject.__init__":
                    pass

                elif command_data[0] == "PageResponseObject.url":
                    response.url = command_data[1].decode()

                elif command_data[0] == "PageResponseObject.headers":
                    try:
                        response.headers = json.loads(command_data[1].decode())
                    except Exception as E:
                        WebLogger.exc(
                            E, "Cannot load response headers from crawling server"
                        )

                elif command_data[0] == "PageResponseObject.status_code":
                    try:
                        response.status_code = int(command_data[1].decode())
                    except Exception as E:
                        WebLogger.exc(E, "Cannot load status_code from crawling server")

                elif command_data[0] == "PageResponseObject.text":
                    response.set_text(command_data[1].decode())

                elif command_data[0] == "PageResponseObject.request_url":
                    response.request_url = command_data[1].decode()

                elif command_data[0] == "PageResponseObject.__del__":
                    break

                elif command[0] == "commands.debug":
                    pass

                elif command[0] == "debug.requests":
                    pass

                else:
                    WebLogger.error("Unsupported command:{}".format(command_data[0]))
                    break

            if connection.is_closed():
                break

            diff = DateUtils.get_datetime_now_utc() - script_time_start
            if diff.total_seconds() > request.timeout_s:
                WebLogger.error("Url:{} Timeout on socket connection:{}/{}".format(request.url, diff.total_seconds(), request.timeout_s))

                response = PageResponseObject(
                    request.url,
                    text=None,
                    status_code=HTTP_STATUS_CODE_TIMEOUT,
                    request_url=request.url,
                )
                break

        connection.close()

        return response

    def get_contents_via_script(self, script, request):
        """
        TODO There might be collision if apache and celery called same script at the same time.
        """
        import os
        from pathlib import Path

        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)

        if HttpPageHandler.script_operating_dir is None:
            operating_path = full_path.parents[1]
        else:
            operating_path = Path(HttpPageHandler.script_operating_dir)

        file_name_url_part = fix_path_for_os(request.url)
        file_name_url_part = file_name_url_part.replace("\\", "")
        file_name_url_part = file_name_url_part.replace("/", "")
        file_name_url_part = file_name_url_part.replace("@", "")

        response_file_location = "response_{}.txt".format(file_name_url_part)

        if HttpPageHandler.script_responses_directory is not None:
            response_dir = Path(HttpPageHandler.script_responses_directory)
            response_dir.mkdir(parents=True, exist_ok=True)

            response_file_location = response_dir / response_file_location

        script = script + ' --url "{}" --output-file="{}"'.format(request.url, str(response_file_location))

        if response_file_location.exists():
            response_file_location.unlink()

        # WebLogger.debug(operating_path)
        # WebLogger.debug(response_file_location)

        WebLogger.info(
            "Url:{} Running script:{} Request:{}".format(request.url, script, request)
        )

        p = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            cwd=operating_path,
            timeout=request.timeout_s,
        )

        if p.returncode != 0:
            if p.stdout:
                stdout_str = p.stdout.decode()
                if stdout_str != "":
                    WebLogger.debug(stdout_str)

            if p.stderr:
                stderr_str = p.stderr.decode()
                if stderr_str and stderr_str != "":
                    WebLogger.error("Url:{}. {}".format(request.url, stderr_str))

            WebLogger.error(
                "Url:{}. Return code invalid:{}".format(
                    request.url, p.returncode
                )
            )

        if response_file_location.exists():
            with open(str(response_file_location), "rb") as fh:
                all_bytes = fh.read()

                response = get_response_from_bytes(all_bytes)

                response_file_location.unlink()
                return response

        else:
            WebLogger.error(
                "Url:{}. Response file does not exist:{}".format(
                    request.url, str(response_file_location)
                )
            )

        return PageResponseObject(
            request.url,
            text=None,
            status_code=HTTP_STATUS_CODE_EXCEPTION,
            request_url=request.url,
        )

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
                    "Url:{}. Options:{} Requesting page: DONE".format(self.url, self.options)
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

    crawling_headless_script = None
    crawling_full_script = None
    crawling_server_port = None

    script_operating_dir = None
    script_responses_directory = Path("storage")

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

        if self.options.use_browser_promotions and self.is_advanced_processing_possible():
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
            """
            """

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
