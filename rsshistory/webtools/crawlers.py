import requests
import json

from .webtools import (
    RssPage,
    HtmlPage,
    PageResponseObject,
    WebLogger,
    PAGE_TOO_BIG_BYTES,
    HTTP_STATUS_CODE_EXCEPTION,
    HTTP_STATUS_CODE_CONNECTION_ERROR,
    HTTP_STATUS_CODE_TIMEOUT,
    HTTP_STATUS_CODE_FILE_TOO_BIG,
    HTTP_STATUS_CODE_PAGE_UNSUPPORTED,
)


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


class RequestsPage(object):
    """
    Python requests crawler interface
    # TODO rename to RequestCrawler
    """

    def __init__(self, request):
        """
        Wrapper for python requests.
        """
        self.request = request
        self.response = None

        WebLogger.debug("Requests GET:{}".format(self.request.url))

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
                headers=request_result.headers,
                request_url=self.request.url,
            )

            if not self.response.is_valid():
                return

            content_length = self.response.get_content_length()
            if content_length > PAGE_TOO_BIG_BYTES:
                self.response.status_code = status_code = HTTP_STATUS_CODE_FILE_TOO_BIG
                self.response.add_error("Page is too big")
                return

            if self.request.ping:
                return

            # TODO do we want to check also content-type?

            content_type = self.response.get_content_type()

            if content_type and not self.response.is_content_type_supported():
                self.response.status_code = HTTP_STATUS_CODE_PAGE_UNSUPPORTED
                self.response.add_error(
                    "Url:{} is not supported {}".format(self.request.url, content_type)
                )
                return

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
                headers=request_result.headers,
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
    """
    Selenium chrome headless
    """

    def get_driver(self):
        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--lang={}".format("en-US"))

        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(service=service, options=options)
        return driver

    def __init__(self, request):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        self.request = request
        self.response = None

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 10

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(self.request.url)
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            status_code = self.get_selenium_status_code(driver)

            headers = self.get_selenium_headers(driver)
            WebLogger.debug("Selenium headers:{}\n{}".format(self.request.url, headers))

            html_content = driver.page_source

            # TODO use selenium wire to obtain status code & headers?

            self.response = PageResponseObject(
                driver.current_url,
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
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response


class SeleniumChromeFull(SeleniumDriver):
    """
    Selenium chrome full - TODO
    """

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

        return webdriver.Chrome(service=service, options=options)

    def __init__(self, request):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
        """
        self.request = request
        self.response = None

        import os

        os.environ["DISPLAY"] = ":10.0"

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 20

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(self.request.url)

            status_code = self.get_selenium_status_code(driver)

            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = driver.page_source

            self.response = PageResponseObject(
                driver.current_url,
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
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response


class SeleniumUndetected(object):
    """
    Selenium undetected
    """

    def get_driver(self):
        import undetected_chromedriver as uc

        service = Service(executable_path="/usr/bin/chromedriver")

        options = uc.ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})
        options.add_argument("--lang={}".format("en-US"))

        return uc.Chrome(service=service, options=options)

    def __init__(self, request):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        This does not work on raspberry pi
        """
        self.request = request
        self.response = None

        driver = self.get_driver()

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = self.request.timeout_s + 20

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(self.request.url)

            status_code = self.get_selenium_status_code(driver)

            """
            TODO - if webpage changes link, it should also update it in this object
            """

            page_source = driver.page_source

            self.response = PageResponseObject(
                driver.current_url,
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
        finally:
            driver.quit()

    def get(self):
        if self.response:
            return self.response
