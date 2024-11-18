"""
TODO
these scripts will not work in case of multithreaded app
"""

import os
from pathlib import Path
from .webtools import WebLogger

from .crawlers import (
    selenium_feataure_enabled,
    RequestsCrawler,
    SeleniumChromeHeadless,
    SeleniumChromeFull,
    SeleniumUndetected,
    ScriptCrawler,
    ServerCrawler,
    SeleniumBase,
)


class WebConfig(object):
    """
    API to configure webtools
    """

    script_operating_dir = None
    script_responses_directory = Path("storage")

    browser_mapping = {}

    def init():
        pass

    def get_browsers():
        return [
            "RequestsCrawler",
            "SeleniumChromeHeadless",  # requires driver location
            "SeleniumChromeFull",  # requires driver location
            "SeleniumUndetected",  # requires driver location
            "ScriptCrawler",  # requires script
            "ServerCrawler",  # requires script & port
            "SeleniumBase",
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
        elif input_string == "SeleniumUndetected":
            return SeleniumUndetected
        elif input_string == "SeleniumBase":
            return SeleniumBase
        elif input_string == "ScriptCrawler":
            return ScriptCrawler
        elif input_string == "ServerCrawler":
            return ServerCrawler

    def get_crawler_from_mapping(request, mapping_data):
        crawler = WebConfig.get_crawler_from_string(mapping_data["crawler"])
        if not crawler:
            return

        settings = mapping_data["settings"]

        c = crawler(request=request, settings=settings)
        if c.is_valid():
            return c

    def get_init_crawler_config(headless_script=None, full_script=None, port=None):
        """
        Caller may provide scripts
        """
        mapping = []

        # one of the methods should be available
        from .ipc import DEFAULT_PORT, SocketConnection

        if not port:
            port = DEFAULT_PORT

            c = SocketConnection()
            if not c.connect(host=SocketConnection.gethostname(), port=port):
                port = None
                c.close()

        try:
            import os
            from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler

            poetry_path = ""
            if "POETRY_ENV" in os.environ:
                poetry_path = os.environ["POETRY_ENV"] + "/bin/"

            if full_script is None:
                full_script = poetry_path + "poetry run python crawleebeautifulsoup.py"
            if headless_script is None:
                headless_script = (
                    poetry_path + "poetry run python crawleebeautifulsoup.py"
                )
        except:
            pass

        mapping.append(WebConfig.get_requests())
        mapping.append(WebConfig.get_scriptcralwer(headless_script, "CrawleeScript"))
        mapping.append(WebConfig.get_servercralwer(port, headless_script, "CrawleeServer"))
        mapping.append(WebConfig.get_scriptcralwer(full_script, "PlaywrightScript"))
        mapping.append(WebConfig.get_servercralwer(port, full_script, "PlaywrightServer"))
        mapping.append(WebConfig.get_seleniumundetected())
        mapping.append(WebConfig.get_seleniumbase())
        mapping.append(WebConfig.get_seleniumheadless())
        mapping.append(WebConfig.get_seleniumfull())

        return mapping

    def get_requests():
        return {
            "enabled"   : True,
            "name"      : "RequestsCrawler",
            "crawler"   : "RequestsCrawler",
            "settings"  : {"timeout_s": 20},
        }

    def get_scriptcralwer(script, name=""):
        if script:
            return {
                "enabled"   : True,
                "name"      : name,
                "crawler"   : "ScriptCrawler",
                "settings"  : {"script": script, "timeout_s": 40},
            }
        else:
            return {
                "enabled"   : False,
                "name"      : name,
                "crawler"   : "ScriptCrawler",
                "settings"  : {"script": script, "timeout_s": 40},
            }

    def get_servercralwer(port, script, name=""):
        if port and script:
            return {
                "enabled"   : False,
                "name"      : name,
                "crawler"   : "ServerCrawler",
                "settings"  : {"port": port, "script": script, "timeout_s": 40},
            }
        else:
            return {
                "enabled"   : False,
                "name"      : name,
                "crawler"   : "ServerCrawler",
                "settings"  : {"port": port, "script": script, "timeout_s": 40},
            }

    def get_seleniumheadless():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled"   : False,
                "name"      : "SeleniumChromeHeadless",
                "crawler"   : "SeleniumChromeHeadless",
                "settings"  : {
                    "driver_executable": str(chromedriver_path),
                    "timeout_s": 30,
                },
            }
        else:
            return {
                "enabled"   : True,
                "name"      : "SeleniumChromeHeadless",
                "crawler"   : "SeleniumChromeHeadless",
                "settings"  : {"driver_executable": None, "timeout_s": 40},
            }

    def get_seleniumfull():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled"   : False,
                "name"      : "SeleniumChromeFull",
                "crawler"   : "SeleniumChromeFull",
                "settings"  : {
                    "driver_executable": str(chromedriver_path),
                    "timeout_s": 40,
                },
            }
        else:
            return {
                "enabled"   : False,
                "name"      : "SeleniumChromeFull",
                "crawler"   : "SeleniumChromeFull",
                "settings"  : {"driver_executable": None, "timeout_s": 40},
            }

    def get_seleniumundetected():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled"   : False,
                "name"      : "SeleniumUndetected",
                "crawler"   : "SeleniumUndetected",
                "settings"  : {
                    "driver_executable": str(chromedriver_path),
                    "timeout_s": 30,
                },
            }
        else:
            return {
                "enabled"   : False,
                "name"      : "SeleniumUndetected",
                "crawler"   : "SeleniumUndetected",
                "settings"  : {"driver_executable": None, "timeout_s": 40},
            }

    def get_seleniumbase():
        return {
            "enabled"   : False,
            "name"      : "SeleniumBase",
            "crawler"   : "SeleniumBase",
            "settings"  : {
            },
        }

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from utils.logger import PrintLogger

        WebLogger.web_logger = PrintLogger
