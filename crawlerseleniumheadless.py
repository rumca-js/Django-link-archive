import json
import time
import argparse

import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from rsshistory import webtools
import crawlerscript


PAGE_TOO_BIG_BYTES = 5000000  # 5 MB


class SeleniumDriver(crawlerscript.ScriptCrawlerInterface):
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
    def __init__(self, parser, request):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        super().__init__(parser, request)

        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # if not RequestBuilder.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(service=service, options=options)

        response = PageResponseObject(self.request.url)

        try:
            driver.set_page_load_timeout(self.request.timeout_s)

            driver.get(url)
            """
            TODO - if webpage changes link, it should also update it in this object
            """

            status_code = self.get_selenium_status_code(driver)

            # if self.options.link_redirect:
            #    WebDriverWait(driver, selenium_timeout).until(EC.url_changes(driver.current_url))

            html_content = driver.page_source

            if self.request.url != driver.current_url:
                response.url = driver.current_url

            # TODO use selenium wire to obtain status code & headers?

            response.set_text(html_content)
            response.status_code = status_code

        except TimeoutException:
            response.set_binary(None)

        finally:
            driver.quit()

        self.response = response

    def get(self):
        return self.response


def main():
    parser = crawlerscript.Parser()
    parser.parse()
    if not parser.is_valid():
        return

    request = parser.get_request()

    page = SeleniumHeadless(parser, request)
    response = page.get()

    print(f'Processing {parser.args.url} ...DONE')

    i.response = response
    i.save_response()


main()
