"""
Simple scraping script.
"""
import socket
import json
import traceback
import asyncio
import time
import requests

from webtools import (
   Url,
   RssPage,
   HtmlPage,
   fetch_url,
   fetch_all_urls,
   WebConfig,
   HttpPageHandler,
   ScrapingClient,
)
from utils.serializers import PageDisplay, PageDisplayParser


__version__ = "0.0.1"


async def main():
    WebConfig.use_print_logging()

    # if scraping server is running, use it
    c = ScrapingClient()
    c.set_scraping_script("poetry run python crawleebeautifulsoup.py")
    if c.connect():
        c.close()
        HttpPageHandler.crawling_server_port = c.port
    else:
        HttpPageHandler.crawling_server_port = 0

    # scraping server is not running, we do not use port
    #HttpPageHandler.crawling_full_script = None
    #HttpPageHandler.crawling_headless_script = None

    HttpPageHandler.crawling_full_script = "poetry run python crawleebeautifulsoup.py"
    HttpPageHandler.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"

    #HttpPageHandler.crawling_full_script = "poetry run python crawlerseleniumundetected.py"
    #HttpPageHandler.crawling_headless_script = "poetry run python crawlerseleniumundetected.py"

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
