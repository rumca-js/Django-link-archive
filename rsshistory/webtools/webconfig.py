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

    def get_modes():
        return ["standard", "headless", "full"]

    def get_browsers():
        return [
            "RequestsCrawler",
            "SeleniumChromeHeadless",  # requires driver location
            "SeleniumChromeFull",  # requires driver location
            "SeleniumUndetected",  # requires driver location
            "ScriptCrawler",  # requires script
            "ServerCrawler",  # requires script & port
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
        mapping = {}

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

        std_preference_table = []

        std_preference_table.append(WebConfig.get_requests())
        std_preference_table.append(WebConfig.get_servercralwer(port, headless_script))
        std_preference_table.append(WebConfig.get_scriptcralwer(headless_script))
        std_preference_table.append(WebConfig.get_seleniumheadless())
        std_preference_table.append(WebConfig.get_servercralwer(port, full_script))
        std_preference_table.append(WebConfig.get_scriptcralwer(full_script))
        std_preference_table.append(WebConfig.get_seleniumfull())
        std_preference_table.append(WebConfig.get_seleniumundetected())

        mapping["standard"] = std_preference_table

        # one of the methods should be available

        headless_preference_table = []

        headless_preference_table.append(
            WebConfig.get_servercralwer(port, headless_script)
        )
        headless_preference_table.append(WebConfig.get_scriptcralwer(headless_script))
        headless_preference_table.append(WebConfig.get_seleniumheadless())
        headless_preference_table.append(WebConfig.get_servercralwer(port, full_script))
        headless_preference_table.append(WebConfig.get_scriptcralwer(full_script))
        headless_preference_table.append(WebConfig.get_seleniumfull())
        headless_preference_table.append(WebConfig.get_requests())
        headless_preference_table.append(WebConfig.get_seleniumundetected())

        mapping["headless"] = headless_preference_table

        # one of the methods should be available

        full_preference_table = []

        full_preference_table.append(WebConfig.get_servercralwer(port, full_script))
        full_preference_table.append(WebConfig.get_scriptcralwer(full_script))
        full_preference_table.append(WebConfig.get_seleniumfull())
        full_preference_table.append(WebConfig.get_servercralwer(port, headless_script))
        full_preference_table.append(WebConfig.get_scriptcralwer(headless_script))
        full_preference_table.append(WebConfig.get_seleniumheadless())
        full_preference_table.append(WebConfig.get_requests())
        full_preference_table.append(WebConfig.get_seleniumundetected())

        mapping["full"] = full_preference_table

        return mapping

    def get_requests():
        return {"enabled": True, "crawler": "RequestsCrawler", "settings": {}}

    def get_servercralwer(port, script):
        if port and script:
            return {
                "enabled": True,
                "crawler": "ServerCrawler",
                "settings": {"port": port, "script": script},
            }
        else:
            return {
                "enabled": False,
                "crawler": "ServerCrawler",
                "settings": {"port": port, "script": script},
            }

    def get_scriptcralwer(script):
        if script:
            return {
                "enabled": True,
                "crawler": "ScriptCrawler",
                "settings": {"script": script},
            }
        else:
            return {
                "enabled": False,
                "crawler": "ScriptCrawler",
                "settings": {"script": script},
            }

    def get_seleniumheadless():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled": True,
                "crawler": "SeleniumChromeHeadless",
                "settings": {"driver_executable": str(chromedriver_path)},
            }
        else:
            return {
                "enabled": True,
                "crawler": "SeleniumChromeHeadless",
                "settings": {"driver_executable": None},
            }

    def get_seleniumfull():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled": True,
                "crawler": "SeleniumChromeFull",
                "settings": {"driver_executable": str(chromedriver_path)},
            }
        else:
            return {
                "enabled": True,
                "crawler": "SeleniumChromeFull",
                "settings": {"driver_executable": None},
            }

    def get_seleniumundetected():
        chromedriver_path = Path("/usr/bin/chromedriver")

        if chromedriver_path.exists():
            return {
                "enabled": True,
                "crawler": "SeleniumUndetected",
                "settings": {"driver_executable": str(chromedriver_path)},
            }
        else:
            return {
                "enabled": True,
                "crawler": "SeleniumUndetected",
                "settings": {"driver_executable": None},
            }

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from utils.logger import PrintLogger

        WebLogger.web_logger = PrintLogger
