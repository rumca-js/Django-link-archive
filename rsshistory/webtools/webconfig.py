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

    def get_init_crawler_config():
        mapping = {}

        # one of the methods should be available

        std_preference_table = [
                {"crawler" : "RequestsCrawler", "settings":{}},
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_headless_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_headless_script}},
                {"crawler" : "SeleniumChromeHeadless", "settings":{"driver_executable" : "/usr/local/bin"}},
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_full_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_full_script}},
                {"crawler" : "SeleniumChromeFull", "settings" : {"driver_executable" : "/usr/local/bin"}},
        ]

        mapping["standard"] = std_preference_table

        # one of the methods should be available

        headless_preference_table = [
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_headless_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_headless_script}},
                {"crawler" : "SeleniumChromeHeadless", "settings":{"driver_executable" : "/usr/local/bin"}},
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_full_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_full_script}},
                {"crawler" : "SeleniumChromeFull", "settings" : {"driver_executable" : "/usr/local/bin"}},
                {"crawler" : "RequestsCrawler", "settings" : {}},
        ]

        mapping["headless"] = headless_preference_table

        # one of the methods should be available

        full_preference_table = [
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_full_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_full_script}},
                {"crawler" : "SeleniumChromeFull", "settings" : {"driver_executable" : "/usr/local/bin"}},
                {"crawler" : "ServerCrawler", "settings":{"port": WebConfig.crawling_server_port, "script" : WebConfig.crawling_headless_script }},
                {"crawler" : "ScriptCrawler", "settings":{"script" : WebConfig.crawling_headless_script}},
                {"crawler" : "SeleniumChromeHeadless", "settings":{"driver_executable" : "/usr/local/bin"}},
                {"crawler" : "RequestsCrawler", "settings" : {}},
        ]

        mapping["full"] = full_preference_table

        return mapping

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from utils.logger import PrintLogger
        WebLogger.web_logger = PrintLogger
