"""
This is manual test. Should be run manually.

I am using poetry, so should you.

In case of doubts copy even more code from web tools.
"""

import json
import time

import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


PAGE_TOO_BIG_BYTES = 5000000  # 5 MB

user_agent = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/116.0"
)

headers = {
    "User-Agent": user_agent,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Charset": "utf-8,ISO-8859-1;q=0.7,*;q=0.3",
    "Accept-Encoding": "none",
    "Accept-Language": "en-US,en;q=0.8",
    "Connection": "keep-alive",
}


class PageResponseObject(object):
    STATUS_CODE_OK = 200
    STATUS_CODE_ERROR = 500
    STATUS_CODE_UNDEF = 0

    def __init__(
        self, url, text, status_code=STATUS_CODE_OK, encoding="utf-8", headers=None
    ):
        self.url = url
        self.status_code = status_code

        self.apparent_encoding = encoding

        self.content = text
        # decoded text
        self.text = text

        # I read selenium always assume utf8 encoding

        # encoding = chardet.detect(contents)['encoding']
        # self.apparent_encoding = encoding
        # self.encoding = encoding

        self.encoding = encoding

        if not headers:
            self.headers = {}
        else:
            self.headers = headers

    def get_content_type(self):
        if "Content-Type" in self.headers:
            return self.headers["Content-Type"]

        # we have to assume something
        return "text"

    def get_content_type_charset(self):
        content = self.get_content_type()
        if not content:
            return

        elements = content.split(";")
        for element in elements:
            wh = element.find("charset")
            if wh >= 0:
                charset_elements = element.split("=")
                if len(charset_elements) > 1:
                    return charset_elements[1]

    def is_content_html(self):
        content = self.get_content_type()
        if not content:
            return False

        if content.lower().find("html") >= 0:
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

        AppLogging.error(
            "Page {} content type is not supported {}".format(self.url, content_type)
        )

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
        403 is added since some pages use it to block you
        """
        return (
            self.status_code > 300 and self.status_code < 400
        ) or self.status_code == 403

    def is_this_status_nok(self):
        """
        This function informs that status code is so bad, that further communication does not make any sense
        """
        return self.status_code < 200 or self.status_code > 403

    def is_valid(self):
        content_length = self.get_content_length()

        if content_length > PAGE_TOO_BIG_BYTES:
            return False

        if not self.is_content_type_supported():
            return False

        if self.is_this_status_nok():
            return False

        return True


class RequestsPage(object):
    def __init__(self, url, headers, timeout_s=10, ping=False):
        """
        This is program is web scraper. If we turn verify, then we discard some of pages.
        Encountered several major pages, which had SSL programs.

        SSL is mostly important for interacting with pages. During web scraping it is not that useful.
        """
        print("Requests GET:{}".format(url))
        self.url = url

        """
        stream argument allows us to read header before we fetch the page.
        SSL verification makes everything to work slower.
        """

        try:
            request_result = self.build_requests(url, headers, timeout_s)

            self.response = PageResponseObject(
                url=url,
                text="",
                status_code=request_result.status_code,
                headers=request_result.headers,
            )

            if not self.response.is_valid():
                return

            # TODO do we want to check also content-type?

            if ping:
                return self.response

            encoding = self.get_encoding(request_result, self.response)
            if encoding:
                request_result.encoding = encoding

            if self.url != request_result.url:
                self.url = request_result.url

            self.response = PageResponseObject(
                url=self.url,
                text=request_result.text,
                status_code=request_result.status_code,
                encoding=request_result.encoding,
                headers=request_result.headers,
            )

        except requests.Timeout:
            LinkDatabase.error("Page timeout {}".format(self.url))
            self.response = PageResponseObject(self.url, None, 500)

    def get(self):
        return self.response

    def get_encoding(self, request_result, response):
        """
        The default assumed content encoding for text/html is ISO-8859-1 aka Latin-1 :( See RFC-2854. UTF-8 was too young to become the default, it was born in 1993, about the same time as HTML and HTTP.
        Use .content to access the byte stream, or .text to access the decoded Unicode stream.

        chardet does not work on youtube RSS feeds.
        apparent encoding does not work on youtube RSS feeds.
        """

        url = self.url

        # There might be several encoding texts, if so we do not know which one to use
        text = request_result.text.lower()

        set_encoding = False

        encoding = response.get_content_type_charset()
        if encoding:
            request_result.encoding = encoding
        else:
            if response.is_content_html():
                p = HtmlPage(url, request_result.text)
                if p.is_valid():
                    if p.get_charset():
                        return p.get_charset()

            if text.count("encoding") == 1 and text.find('encoding="utf-8"') >= 0:
                return "utf-8"
            elif text.count("charset") == 1 and text.find('charset="utf-8"') >= 0:
                return "utf-8"

        if not set_encoding:
            return request_result.apparent_encoding

    def build_requests(self, url, headers, timeout_s):
        request_result = requests.get(
            url,
            headers=headers,
            timeout=timeout_s,
            verify=False,
            stream=True,
        )
        print("[H] {}".format(request_result.headers))
        return request_result


class SeleniumDriver(object):
    def get_selenium_status_code(self, driver):
        status_code = 200
        try:
            logs = driver.get_log("performance")
            status_code2 = self.get_selenium_status_code_from_logs(logs)
            if status_code2:
                status_code = status_code2
        except Exception as E:
            AppLogging.error("Chrome webdrider error:{}".format(str(E)))
        return status_code

    def get_selenium_status_code_from_logs(self, logs):
        """
        https://stackoverflow.com/questions/5799228/how-to-get-status-code-by-using-selenium-py-python-code
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
                    # print("Exception: {}".format(str(E)))
                    pass

        return last_status_code


class SeleniumHeadless(SeleniumDriver):
    def __init__(self, url, headers, timeout_s=10):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        self.url = url

        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # if not BasePage.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(service=service, options=options)

        try:
            # add 10 seconds for start of browser, etc.
            selenium_timeout = timeout_s + 10

            driver.set_page_load_timeout(selenium_timeout)

            driver.get(url)
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            status_code = self.get_selenium_status_code(driver)

            # if self.options.link_redirect:
            #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

            html_content = driver.page_source

            if self.url != driver.current_url:
                self.url = driver.current_url

            # TODO use selenium wire to obtain status code & headers?

            self.response = PageResponseObject(self.url, html_content, status_code)
        except TimeoutException:
            error_text = traceback.format_exc()
            LinkDatabase.error("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(self.url, None, 500)
        finally:
            driver.quit()

    def get(self):
        return self.response


class SeleniumFull(object):
    def __init__(self, url, headers, timeout_s):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        https://stackoverflow.com/questions/50642308/webdriverexception-unknown-error-devtoolsactiveport-file-doesnt-exist-while-t
        """
        self.url = url

        import os

        os.environ["DISPLAY"] = ":10.0"

        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--remote-debugging-pipe')
        # options.add_argument('--remote-debugging-port=9222')
        # options.add_argument('--user-data-dir=~/.config/google-chrome')

        # options to enable performance log, to read status code
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # if not BasePage.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(service=service, options=options)

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

            self.response = PageResponseObject(self.url, page_source, status_code)

        except TimeoutException:
            error_text = traceback.format_exc()
            LinkDatabase.error("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(self.url, None, 500)
        finally:
            driver.quit()

    def get(self):
        return self.response


class SeleniumUndetected(object):
    def __init__(url, headers, timeout_s=10):
        """
        To obtain RSS page you have to run real, full blown browser.

        It may require some magic things to make the browser running.

        This does not work on raspberry pi
        """
        self.url = url

        import undetected_chromedriver as uc

        options = uc.ChromeOptions()
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = uc.Chrome(options=options)

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

            self.response = PageResponseObject(self.url, page_source, status_code)

        except TimeoutException:
            error_text = traceback.format_exc()
            LinkDatabase.error("Page timeout:{}\n{}".format(self.url, error_text))
            self.response = PageResponseObject(self.url, None, 500)
        finally:
            driver.quit()

    def get(self):
        return self.response


def get_selenium_status_code(logs):
    """
    https://stackoverflow.com/questions/5799228/how-to-get-status-code-by-using-selenium-py-python-code
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
                response_received = d["message"]["method"] == "Network.responseReceived"
                if content_type.find("text/html") >= 0 and response_received:
                    last_status_code = d["message"]["params"]["response"]["status"]
            except Exception as E:
                # print("Exception: {}".format(str(E)))
                pass

    return last_status_code


def selenium_headless(url, timeout=10):
    service = Service(executable_path="/usr/bin/chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")

    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 10

    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    # if self.options.link_redirect:
    #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

    html_content = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    # print(html_content)
    print(status_code)

    driver.quit()

    return html_content


def selenium_full(url, timeout=10):
    import os

    # from pyvirtualdisplay import Display

    # display = Display(visible=0, size=(800, 600))
    # display.start()

    os.environ["DISPLAY"] = ":10.0"

    service = Service(executable_path="/usr/bin/chromedriver")

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # options.add_argument("--disable-setuid-sandbox")
    # options.add_argument("--remote-debugging-port=9222")  # this
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("start-maximized")
    # options.add_argument("disable-infobars")
    # options.add_argument(r"user-data-dir=\home\rumpel\cookies\\")

    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument('--remote-debugging-pipe')
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--user-data-dir=~/.config/google-chrome')

    # options to enable performance log, to read status code
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # if not BasePage.ssl_verify:
    #    options.add_argument('ignore-certificate-errors')

    driver = webdriver.Chrome(service=service, options=options)

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 20

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    WebDriverWait(driver, selenium_timeout)
    import time

    time.sleep(10)

    ## if self.options.link_redirect:
    # WebDriverWait(driver, selenium_timeout).until(
    #    EC.url_changes(driver.current_url)
    # )
    """
    TODO - if webpage changes link, it should also update it in this object
    """

    page_source = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(page_source)

    driver.quit()


def selenium_undetected(url, timeout=10):
    service = Service(executable_path="/usr/bin/chromedriver")
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    #
    # options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 10

    driver = webdriver.Chrome(service=service, options=options)

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)
    time.sleep(timeout + 7)

    status_code = 200

    # if self.options.link_redirect:
    #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

    html_content = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(html_content)
    print(status_code)

    driver.quit()

    return html_content


def selenium_full(url, timeout=10):
    import os

    # from pyvirtualdisplay import Display

    # display = Display(visible=0, size=(800, 600))
    # display.start()

    os.environ["DISPLAY"] = ":10.0"

    service = Service(executable_path="/usr/bin/chromedriver")

    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # options.add_argument("--disable-setuid-sandbox")
    # options.add_argument("--remote-debugging-port=9222")  # this
    # options.add_argument("--disable-extensions")
    # options.add_argument("--disable-gpu")
    # options.add_argument("start-maximized")
    # options.add_argument("disable-infobars")
    # options.add_argument(r"user-data-dir=\home\rumpel\cookies\\")

    # options.add_argument("--disable-dev-shm-usage")
    # options.add_argument('--remote-debugging-pipe')
    # options.add_argument('--remote-debugging-port=9222')
    # options.add_argument('--user-data-dir=~/.config/google-chrome')

    # options to enable performance log, to read status code
    options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    # if not BasePage.ssl_verify:
    #    options.add_argument('ignore-certificate-errors')

    driver = webdriver.Chrome(service=service, options=options)

    # add 10 seconds for start of browser, etc.
    selenium_timeout = timeout + 20

    driver.set_page_load_timeout(selenium_timeout)

    driver.get(url)

    status_code = 200
    try:
        logs = driver.get_log("performance")
        status_code2 = get_selenium_status_code(logs)
        if status_code2:
            status_code = status_code2
    except Exception as E:
        print("Chrome webdrider error:{}".format(str(E)))

    WebDriverWait(driver, selenium_timeout)
    import time

    time.sleep(10)

    ## if self.options.link_redirect:
    # WebDriverWait(driver, selenium_timeout).until(
    #    EC.url_changes(driver.current_url)
    # )
    """
    TODO - if webpage changes link, it should also update it in this object
    """

    page_source = driver.page_source

    if url != driver.current_url:
        url = driver.current_url

    print(page_source)

    driver.quit()


def main():
    # selenium_full("https://www.warhammer-community.com/en-us/feed")
    # selenium_headless("https://www.warhammer-community.com/")
    # selenium_headless("https://www.google.com/")
    # selenium_undetected("https://www.warhammer-community.com/feed")

    # p = RequestsPage("https://www.google.com/", headers=headers)
    # print(p.get().text)
    # p = SeleniumHeadless("https://www.google.com/", headers=headers)
    # print(p.get().text)
    p = SeleniumUndetected("https://www.google.com/", headers=headers)
    print(p.get().text)


main()
