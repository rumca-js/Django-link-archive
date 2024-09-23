"""
Simple scraping script.
"""
import socket
import json
import traceback
import asyncio
import time
import requests

from rsshistory.webtools import (
   Url,
   RssPage,
   HtmlPage,
   fetch_url,
   fetch_all_urls,
   WebConfig,
   ScrapingClient,
)
from utils.serializers import PageDisplay, PageDisplayParser


__version__ = "0.0.1"


async def main():
    WebConfig.init()
    # we do not want to be swamped with web requests
    # WebConfig.use_print_logging()

    # if scraping server is running, use it
    c = ScrapingClient()
    c.set_scraping_script("poetry run python crawleebeautifulsoup.py")
    if c.connect():
        c.close()
        WebConfig.crawling_server_port = c.port
    else:
        WebConfig.crawling_server_port = 0

    # scraping server is not running, we do not use port
    #WebConfig.crawling_full_script = None
    #WebConfig.crawling_headless_script = None

    WebConfig.crawling_full_script = "poetry run python crawleebeautifulsoup.py"
    WebConfig.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"
    #WebConfig.crawling_full_script = "poetry run python crawlerseleniumundetected.py"
    #WebConfig.crawling_headless_script = "poetry run python crawlerseleniumundetected.py"

    parser = PageDisplayParser()
    parser.parse()

    if not parser.args.url:
        parser.parser.print_help()
    else:
        display = PageDisplay(parser.args.url, verbose = parser.args.verbose, method = parser.args.method)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Done in {time.time() - start_time} seconds")
