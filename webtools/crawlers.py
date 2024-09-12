"""
Provides cralwers implmenetation that can be used directly in program.

Some crawlers / scrapers cannot be easily called from a thread, etc, because of asyncio.
"""

import json
import traceback
from pathlib import Path
import os
import subprocess

from utils.dateutils import DateUtils

from .webtools import (
    RssPage,
    HtmlPage,
    PageResponseObject,
    WebLogger,
    get_request_to_bytes,
    get_response_from_bytes,
    PAGE_TOO_BIG_BYTES,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_CONNECTION_ERROR,
    HTTP_STATUS_CODE_TIMEOUT,
    HTTP_STATUS_CODE_FILE_TOO_BIG,
    HTTP_STATUS_CODE_PAGE_UNSUPPORTED,
)

from .ipc import (
    string_to_command,
    SocketConnection,
)

requests_feataure_enabled = True
try:
    import requests
except Exception as E:
    print(str(E))
    requests_feataure_enabled = False


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


class CrawlerInterface(object):
    def __init__(self, request, response_file=None, response_port=None):
        """
        @param response_file If set, response is stored in a file
        @param response_port If set, response is sent through port
        """
        self.request = request
        self.response = None
        self.response_file = response_file
        self.response_port = response_port

    def run(self):
        """
         - does its job
         - sets self.response
         - clears everything from memory, it created

        @return response, None if feature is not available
        """
        return self.response

    def response_to_bytes(self):
        all_bytes = bytearray()

        if not self.response:
            return all_bytes

        # same as PageResponseObject
        bytes1 = string_to_command("PageResponseObject.__init__", "OK")
        bytes2 = string_to_command("PageResponseObject.url", self.response.url)
        bytes3 = string_to_command(
            "PageResponseObject.request_url", self.response.request_url
        )
        bytes4 = string_to_command(
            "PageResponseObject.status_code", str(self.response.status_code)
        )

        if self.response.text:
            bytes5 = string_to_command("PageResponseObject.text", self.response.text)
        else:
            bytes5 = bytearray()

        bytes6 = string_to_command(
            "PageResponseObject.headers", json.dumps(self.response.headers)
        )
        bytes7 = string_to_command("PageResponseObject.__del__", "OK")

        all_bytes.extend(bytes1)
        all_bytes.extend(bytes2)
        all_bytes.extend(bytes3)
        all_bytes.extend(bytes4)
        all_bytes.extend(bytes5)
        all_bytes.extend(bytes6)
        all_bytes.extend(bytes7)
        return all_bytes

    def get_response(self):
        return self.response

    def save_response(self):
        if not self.response:
            WebLogger.error("Have not received response")
            return False

        all_bytes = self.response_to_bytes()

        if self.response_file:
            path = Path(self.response_file)
            if not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.response_file, "wb") as fh:
                fh.write(all_bytes)

        elif self.response_port:
            con = SocketConnection()
            con.connect(SocketConnection.gethostname(), self.response_port)
            con.send(all_bytes)

        else:
            response = self.get_response()

        return True

    def close(self):
        pass


class RequestsCrawler(CrawlerInterface):
    """
    Python requests
    """

    def __init__(self, request, response_file=None, response_port=None):
        """
        Wrapper for python requests.
        """
        super().__init__(
            request, response_file=response_file, response_port=response_port
        )

    def run(self):
        if not requests_feataure_enabled:
            return

        WebLogger.debug("Requests Driver:{}".format(self.request.url))

        """
        stream argument allows us to read header before we fetch the page.
        SSL verification makes everything to work slower.
        """

        try:
            request_result = self.build_requests()

            self.response = PageResponseObject(
                url=request_result.url,
                text="",
                status_code=request_result.status_code,
                headers=dict(request_result.headers),
                request_url=self.request.url,
            )

            if not self.response.is_valid():
                return self.response

            content_length = self.response.get_content_length()
            if content_length > PAGE_TOO_BIG_BYTES:
                self.response.status_code = status_code = HTTP_STATUS_CODE_FILE_TOO_BIG
                self.response.add_error("Page is too big")
                return self.response

            if self.request.ping:
                return self.response

            # TODO do we want to check also content-type?

            content_type = self.response.get_content_type()

            if content_type and not self.response.is_content_type_supported():
                self.response.status_code = HTTP_STATUS_CODE_PAGE_UNSUPPORTED
                self.response.add_error(
                    "Url:{} is not supported {}".format(self.request.url, content_type)
                )
                return self.response

            """
            IF we do not know the content type, or content type is supported
            """
            encoding = self.get_encoding(request_result, self.response)
            if encoding:
                request_result.encoding = encoding

            self.response = PageResponseObject(
                url=request_result.url,
                text=request_result.text,
                status_code=request_result.status_code,
                encoding=request_result.encoding,
                headers=dict(request_result.headers),
                binary=request_result.content,
                request_url=self.request.url,
            )

        except requests.Timeout:
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_TIMEOUT,
                request_url=self.request.url,
            )
            self.response.add_error("Url:{} Page timeout".format(self.request.url))

        except requests.exceptions.ConnectionError:
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_CONNECTION_ERROR,
                request_url=self.request.url,
            )
            self.response.add_error("Url:{} Connection error".format(self.request.url))

        except Exception as E:
            WebLogger.exc(E, "Url:{} General exception".format(self.request.url))

            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_EXCEPTION,
                request_url=self.request.url,
            )
            self.response.add_error("General page exception")

        return self.response

    def get_encoding(self, request_result, response):
        """
        The default assumed content encoding for text/html is ISO-8859-1 aka Latin-1 :( See RFC-2854. UTF-8 was too young to become the default, it was born in 1993, about the same time as HTML and HTTP.
        Use .content to access the byte stream, or .text to access the decoded Unicode stream.

        chardet does not work on youtube RSS feeds.
        apparent encoding does not work on youtube RSS feeds.
        """

        url = self.request.url

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

    def build_requests(self):
        """
        stream argument - will fetch page contents, when we access contents of page.
        """

        request_result = requests.get(
            self.request.url,
            headers=self.request.headers,
            timeout=self.request.timeout_s,
            verify=self.request.ssl_verify,
            stream=True,
        )

        return request_result


class StealthRequestsCrawler(CrawlerInterface):
    """
    Python steath requests
    """

    def __init__(self, request, response_file=None, response_port=None):
        """
        Wrapper for python requests.
        """
        super().__init__(
            request, response_file=response_file, response_port=response_port
        )

    def run(self):
        try:
            import stealth_requests as requests
        except Exception as E:
            print("Cannot import stealth_requests")
            return

        answer = requests.get(self.request.url)

        if answer and answer.content:
            self.response = PageResponseObject(
                self.request.url,
                binary=answer.content,
                status_code=200,
                request_url=self.request.url,
            )

            return self.response


class SeleniumDriver(CrawlerInterface):
    """
    Everybody uses selenium
    """
    def __init__(self, request, response_file=None, response_port=None, driver_executable = None):
        super().__init__(
            request, response_file=response_file, response_port=response_port
        )
        self.display = None
        self.driver = None
        self.driver_executable = driver_executable

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

        TODO this probably does not work "Correctly"
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

    def close(self):
        try:
            self.driver.close()
        except Exception as E:
            pass

        try:
            self.driver.quit()
        except Exception as E:
            pass

        if self.display:
            self.display.stop()


class SeleniumChromeHeadless(SeleniumDriver):
    """
    Selenium chrome headless
    """

    def get_driver(self):
        try:
            #if not self.driver_executable:
            #    self.driver_executable = "/usr/bin/chromedriver"

            if self.driver_executable:
                p = Path(self.driver_executable)
                if not p.exists():
                    WebLogger.error("We do not have chromedriver executable")
                    return

                service = Service(executable_path=self.driver_executable)
            else:
                service = Service()

            options = webdriver.ChromeOptions()
            options.add_argument("--headless")
            options.add_argument("--lang={}".format("en-US"))

            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

            driver = webdriver.Chrome(service=service, options=options)
            return driver
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            WebLogger.debug("Cannot obtain driver:{}\n{}".format(self.request.url, error_text))

    def run(self):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        if not selenium_feataure_enabled:
            return

        self.driver = self.get_driver()
        if not self.driver:
            return

        WebLogger.debug("SeleniumChromeHeadless Driver:{}".format(self.request.url))

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 10

            self.driver.set_page_load_timeout(selenium_timeout)

            self.driver.get(self.request.url)
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            status_code = self.get_selenium_status_code(self.driver)

            headers = self.get_selenium_headers(self.driver)
            WebLogger.debug("Selenium headers:{}\n{}".format(self.request.url, headers))

            html_content = self.driver.page_source

            # TODO use selenium wire to obtain status code & headers?

            self.response = PageResponseObject(
                self.driver.current_url,
                text=html_content,
                status_code=status_code,
                request_url=self.request.url,
            )
        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.request.url, error_text))
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_TIMEOUT,
                request_url=self.request.url,
            )
        except Exception as E:
            WebLogger.exc(E, "Url:{}".format(self.request.url))
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_EXCEPTION,
                request_url=self.request.url,
            )

        return self.response


class SeleniumChromeFull(SeleniumDriver):
    """
    Selenium chrome full - TODO
    """

    def get_driver(self):
        """
        https://forums.raspberrypi.com/viewtopic.php?t=129320
        """
        try:
            if self.driver_executable:
                p = Path(self.driver_executable)
                if not p.exists():
                    WebLogger.error("We do not have chromedriver executable")
                    return

            # requires xvfb
            import os
            os.environ["DISPLAY"] = ":10.0"
            from pyvirtualdisplay import Display
            self.display = Display(visible=0, size=(800, 600))
            self.display.start()

            if self.driver_executable:
                service = Service(executable_path=str(self.driver_executable))
            else:
                service = Service()

            options = webdriver.ChromeOptions()
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            #options.add_argument("--headless")
            options.add_argument("--lang={}".format("en-US"))

            options.add_argument("start-maximized")
            options.add_argument("disable-infobars")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-gpu")

            # options to enable performance log, to read status code
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

            return webdriver.Chrome(service=service, options=options)
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            WebLogger.debug("Cannot obtain driver:{}\n{}".format(self.request.url, error_text))

    def run(self):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
        """
        if not selenium_feataure_enabled:
            return

        self.driver = self.get_driver()
        if not self.driver:
            return

        WebLogger.debug("SeleniumChromeFull Driver:{}".format(self.request.url))

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 20

            self.driver.set_page_load_timeout(selenium_timeout)

            self.driver.get(self.request.url)

            status_code = self.get_selenium_status_code(self.driver)

            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = self.driver.page_source

            self.response = PageResponseObject(
                self.driver.current_url,
                text=page_source,
                status_code=status_code,
                request_url=self.request.url,
            )

        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.request.url, error_text))
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_TIMEOUT,
                request_url=self.request.url,
            )
        except Exception as E:
            WebLogger.exc(E, "Url:{}".format(self.request.url))
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_EXCEPTION,
                request_url=self.request.url,
            )

        return self.response


class SeleniumUndetected(SeleniumDriver):
    """
    Selenium undetected
    """

    def get_driver(self):
        try:
            """
            NOTE: This driver may not work on raspberry PI
            """
            import undetected_chromedriver as uc

            options = uc.ChromeOptions()
            options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
            options.add_argument("--lang={}".format("en-US"))
            return uc.Chrome(options=options)
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            WebLogger.debug("Cannot obtain driver:{}\n{}".format(self.request.url, error_text))
            return

    def run(self):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        This does not work on raspberry pi
        """

        self.driver = self.get_driver()
        if not self.driver:
            return

        WebLogger.debug("SeleniumUndetected Driver:{}".format(self.request.url))

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 20

            self.driver.set_page_load_timeout(selenium_timeout)

            self.driver.get(self.request.url)

            status_code = self.get_selenium_status_code(self.driver)

            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = self.driver.page_source

            self.response = PageResponseObject(
                self.driver.current_url,
                text=page_source,
                status_code=status_code,
                request_url=self.request.url,
            )

        except TimeoutException:
            error_text = traceback.format_exc()
            WebLogger.debug("Page timeout:{}\n{}".format(self.request.url, error_text))
            self.response = PageResponseObject(
                self.request.url,
                text=None,
                status_code=HTTP_STATUS_CODE_TIMEOUT,
                request_url=self.request.url,
            )

        return self.response


class ScriptCrawler(CrawlerInterface):
    """
    Used to run script to obtain URL response.
    Calls script, and receives reply in the file.

    Note:
     If we have multiple instances/workspaces each can write their own output file
    """
    def __init__(self, request, response_file=None, response_port=None, cwd=None, script=None):
        super().__init__(request = request, response_file = response_file, response_port = response_port)
        self.cwd = cwd
        self.script = script

    def run(self):
        if not self.script:
            return

        file_path = os.path.realpath(__file__)
        full_path = Path(file_path)

        operating_path = self.cwd
        response_file_location = Path(self.response_file)

        if len(response_file_location.parents) > 1:
            response_dir = response_file_location.parents[1]
            if not response_dir.exists():
                response_dir.mkdir(parents=True, exist_ok=True)

        if response_file_location.exists():
            response_file_location.unlink()

        script = self.script + ' --url "{}" --output-file="{}"'.format(
            self.request.url, self.response_file
        )

        # WebLogger.debug(operating_path)
        # WebLogger.debug(response_file_location)

        WebLogger.info(
            "Url:{} Running script:{} Request:{}".format(self.request.url, script, self.request)
        )

        p = subprocess.run(
            script,
            shell=True,
            capture_output=True,
            cwd=operating_path,
            timeout=self.request.timeout_s,
        )

        if p.returncode != 0:
            if p.stdout:
                stdout_str = p.stdout.decode()
                if stdout_str != "":
                    WebLogger.debug(stdout_str)

            if p.stderr:
                stderr_str = p.stderr.decode()
                if stderr_str and stderr_str != "":
                    WebLogger.error("Url:{}. {}".format(self.request.url, stderr_str))

            WebLogger.error(
                "Url:{}. Return code invalid:{}".format(self.request.url, p.returncode)
            )

        if response_file_location.exists():
            response = None 

            with open(str(response_file_location), "rb") as fh:
                all_bytes = fh.read()
                self.response = get_response_from_bytes(all_bytes)

            response_file_location.unlink()
            return self.response

        else:
            WebLogger.error(
                "Url:{}. Response file does not exist:{}".format(
                    self.request.url, str(response_file_location)
                )
            )

    def close(self):
        response_file_location = Path(self.response_file)
        if response_file_location.exists():
            response_file_location.unlink()


class ServerCrawler(CrawlerInterface):
    """
    Used to ask crawling server for URL.
    Sends request to server, and receives reply
    """
    def __init__(self, request, response_file=None, response_port=None, script=None):
        super().__init__(request = request, response_file = response_file, response_port = response_port)
        self.script = script
        self.connection = None

    def run(self):
        if not self.script:
            WebLogger.error("Script was not set in the sever crawler")
            return

        script_time_start = DateUtils.get_datetime_now_utc()

        self.connection = SocketConnection()
        try:
            if not self.connection.connect(SocketConnection.gethostname(), self.response_port):
                WebLogger.error("Cannot connect to port{}".format(self.response_port))

                self.response = PageResponseObject(
                    self.request.url,
                    text=None,
                    status_code=HTTP_STATUS_CODE_CONNECTION_ERROR,
                    request_url=self.request.url,
                )
                return self.response
        except Exception as E:
            WebLogger.exc(E, "Cannot connect to port{}".format(self.response_port))
            return

        bytes = get_request_to_bytes(self.request, self.script)
        self.connection.send(bytes)

        response = PageResponseObject(self.request.url)
        response.status_code = HTTP_STATUS_CODE_TIMEOUT
        response.request_url = self.request.url

        while True:
            command_data = self.connection.get_command_and_data()

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

            if self.connection.is_closed():
                break

            diff = DateUtils.get_datetime_now_utc() - script_time_start
            if diff.total_seconds() > self.request.timeout_s:
                WebLogger.error(
                    "Url:{} Timeout on socket connection:{}/{}".format(
                        self.request.url, diff.total_seconds(), self.request.timeout_s
                    )
                )

                response = PageResponseObject(
                    self.request.url,
                    text=None,
                    status_code=HTTP_STATUS_CODE_TIMEOUT,
                    request_url=self.request.url,
                )
                break

        self.response = response

        return self.response

    def close(self):
        if self.connection:
            self.connection.close()

