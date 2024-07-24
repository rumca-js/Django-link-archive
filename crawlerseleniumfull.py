import json
import time
import argparse

import requests

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from rsshistory.webtools import PageResponseObject


PAGE_TOO_BIG_BYTES = 5000000  # 5 MB


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
    def __init__(self, url, response_file, timeout_s=10, ping=False):
        """
        To obtain RSS page you have to run real, full blown browser.

        Headless might not be enough to fool cloudflare.
        """
        self.url = url

        service = Service(executable_path="/usr/bin/chromedriver")
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")

        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # options.add_argument("--no-sandbox")
        # options.add_argument("--disable-dev-shm-usage")
        # options.add_argument('--remote-debugging-pipe')
        # options.add_argument('--remote-debugging-port=9222')
        # options.add_argument('--user-data-dir=~/.config/google-chrome')

        # if not RequestBuilder.ssl_verify:
        #    options.add_argument('ignore-certificate-errors')

        driver = webdriver.Chrome(service=service, options=options)

        try:
            driver.set_page_load_timeout(timeout_s)

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
            self.response = PageResponseObject(self.url, None, 500)
        finally:
            driver.quit()

    def get(self):
        return self.response



class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--url", help="Directory to be scanned")
        self.parser.add_argument("--timeout", default=10, help="Timeout expressed in seconds")
        self.parser.add_argument("--ping", default=False, help="Ping only")
        self.parser.add_argument("-o", "--output-file", help="Output file")

        self.args = self.parser.parse_args()


def main():
    parser = Parser()
    parser.parse()

    if "url" not in parser.args:
        print("Url file not in args")
        return

    if "output_file" not in parser.args:
        print("Output file not in args")
        return

    if parser.args.url is None:
        print("Url file not in args")
        return

    if parser.args.output_file is None:
        print("Output file not in args")
        return

    page = SeleniumHeadless(parser.args.url, parser.args.output_file, parser.args.timeout, parser.args.ping)
    response = page.get()

    print(f'Processing {parser.args.url} ...DONE')

    all_bytes = response.to_bytes()
    with open(parser.args.output_file, "wb") as fh:
        fh.write(all_bytes)


main()
