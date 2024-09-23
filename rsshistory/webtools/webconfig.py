"""
TODO
these scripts will not work in case of multithreaded app
"""
import os
from pathlib import Path
from utils.basictypes import fix_path_for_os
from .webtools import WebLogger

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
    def __init__(self, request, response_file=None, response_port=None, settings=None):
        self.request = request
        self.script = self.get_script()
        self.process_input()

        super().__init__(request=request, response_file=self.response_file, response_port=response_port, cwd=self.operating_path, settings=settings, script=self.script)

    def get_script(self):
        return WebConfig.crawling_headless_script

    def process_input(self):
        if not self.script:
            self.response_file = None
            self.operating_path = None
            return

        self.operating_path = self.get_operating_dir()
        self.response_file = self.get_response_file_name(self.operating_path)

    def is_valid(self):
        if not self.is_full_script_valid():
            return False

        return True

    def is_full_script_valid(self):
        if not self.script:
            return

        return True

    def get_response_file_name(self, operating_path):
        file_name_url_part = fix_path_for_os(self.request.url)
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
            operating_path = full_path.parents[2]
        else:
            operating_path = Path(WebConfig.script_operating_dir)

        if not operating_path.exists():
            WebLogger.error("Operating path does not exist: {}".format(operating_path))
            return

        return operating_path


class FullScriptCrawler(ScriptCrawler):
    def __init__(self, request, response_file=None, response_port=None, settings=None):
        super().__init__(request=request, response_file=response_file, response_port=response_port, settings=settings)

    def get_script(self):
        return WebConfig.crawling_full_script


class HeadlessServerCrawler(ServerCrawler):
    def __init__(self, request, response_file=None, response_port=None, settings=None):
        script = self.get_script()

        port = self.get_port()
        super().__init__(request=request, response_file=response_file, response_port=port, script=script, settings=settings)

    def get_script(self):
        if not WebConfig.crawling_server_port:
            return

        script = WebConfig.crawling_headless_script
        if script is None:
            script = "poetry run python crawleebeautifulsoup.py"

        return script

    def get_port(self):
        return WebConfig.crawling_server_port


class FullServerCrawler(ServerCrawler):
    def __init__(self, request, response_file=None, response_port=None, settings=None):
        script = self.get_script()

        port = self.get_port()
        super().__init__(request=request, response_file=response_file, response_port=port, script=script, settings=settings)

    def get_script(self):
        if not WebConfig.crawling_server_port:
            return

        script = WebConfig.crawling_full_script
        if script is None:
            script = "poetry run python crawleeplaywright.py"

        return script

    def get_port(self):
        return WebConfig.crawling_server_port


class ConfiguredSeleniumChromeHeadless(SeleniumChromeHeadless):
    def __init__(self, request, response_file=None, response_port=None, driver_executable = None, settings=None):
        driver_executable=WebConfig.selenium_driver_location
        super().__init__(request, response_file=response_file, response_port=response_port, driver_executable = driver_executable, settings=settings)


class ConfiguredSeleniumChromeFull(SeleniumChromeFull):
    def __init__(self, request, response_file=None, response_port=None, driver_executable = None, settings=None):
        driver_executable=WebConfig.selenium_driver_location
        super().__init__(request, response_file=response_file, response_port=response_port, driver_executable = driver_executable, settings=settings)


class WebConfig(object):
    """
    API to configure webtools
    """

    crawling_headless_script = None
    crawling_full_script = None
    crawling_server_port = None

    script_operating_dir = None
    script_responses_directory = Path("storage")
    selenium_driver_location = None

    browser_mapping = {}

    def init():
        p = Path("/usr/bin/chromedriver")
        if p.exists():
            WebConfig.selenium_driver_location = str(p)

    def get_modes():
        return [
           "standard",
           "headless",
           "full"
        ]

    def get_browsers():
        return [
            "RequestsCrawler",
            "SeleniumChromeHeadless", # requires driver location
            "SeleniumChromeFull", # requires driver location
            "ScriptCrawler", # requires script
            "ServerCrawler", # requires script & port
            "HeadlessScriptCrawler",
            "FullScriptCrawler",
            "HeadlessServerCrawler",
            "FullServerCrawler",
            "ConfiguredSeleniumChromeHeadless",
            "ConfiguredSeleniumChromeFull",
        ]

    def get_crawler_from_string(input_string):
        """
        TODO - apply generic approach
        """
        if input_string == "RequestsCrawler":
            return RequestsCrawler
        elif input_string == "SeleniumChromeHeadless":
            return SeleniumChromeHeadless
        elif input_string == "SeleniumChromeFull":
            return SeleniumChromeFull
        elif input_string == "ScriptCrawler":
            return ScriptCrawler
        elif input_string == "ServerCrawler":
            return ServerCrawler
        elif input_string == "HeadlessScriptCrawler":
            return HeadlessScriptCrawler
        elif input_string == "FullScriptCrawler":
            return FullScriptCrawler
        elif input_string == "HeadlessServerCrawler":
            return HeadlessServerCrawler
        elif input_string == "FullServerCrawler":
            return FullServerCrawler
        elif input_string == "ConfiguredSeleniumChromeHeadless":
            return ConfiguredSeleniumChromeHeadless
        elif input_string == "ConfiguredSeleniumChromeFull":
            return ConfiguredSeleniumChromeFull

    def get_init_crawler_config():
        mapping = {}

        std_preference_table = [
                {"crawler" : "RequestsCrawler", "settings":{}},
                {"crawler" : "HeadlessServerCrawler", "settings":{}},
                {"crawler" : "HeadlessScriptCrawler", "settings":{}},
                {"crawler" : "ConfiguredSeleniumChromeHeadless", "settings":{}},
                {"crawler" : "FullServerCrawler", "settings" : {}},
                {"crawler" : "FullScriptCrawler", "settings" : {}},
                {"crawler" : "ConfiguredSeleniumChromeFull", "settings" : {}},
        ]

        mapping["standard"] = std_preference_table

        headless_preference_table = [
                {"crawler" : "HeadlessServerCrawler", "settings" : {}},
                {"crawler" : "HeadlessScriptCrawler", "settings" : {}},
                {"crawler" : "ConfiguredSeleniumChromeHeadless", "settings" : {}},
                {"crawler" : "FullServerCrawler", "settings" : {}},
                {"crawler" : "FullScriptCrawler", "settings" : {}},
                {"crawler" : "ConfiguredSeleniumChromeFull", "settings" : {}},
                {"crawler" : "RequestsCrawler", "settings" : {}},
        ]

        mapping["headless"] = headless_preference_table

        full_preference_table = [
                {"crawler" : "FullServerCrawler", "settings" : {}},
                {"crawler" : "FullScriptCrawler", "settings" : {}},
                {"crawler" : "ConfiguredSeleniumChromeFull", "settings" : {}},
                {"crawler" : "HeadlessServerCrawler", "settings" : {}},
                {"crawler" : "HeadlessScriptCrawler", "settings" : {}},
                {"crawler" : "ConfiguredSeleniumChromeHeadless", "settings" : {}},
                {"crawler" : "RequestsCrawler", "settings" : {}},
        ]

        mapping["full"] = full_preference_table

        return mapping

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from utils.logger import PrintLogger
        WebLogger.web_logger = PrintLogger
