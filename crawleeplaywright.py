"""
I wanted to use crawlee directly in my project
 - I am running code in a thread (not a main thread)
 - crawlee uses asyncio, therefore I also have to use it
 - I tried creating my own loop in a thread, and on windows such system works
 - on linux raspberry it does not. Asyncio does not allow to define new loop from task
    set_wakeup_fd only works in main thread of the main interpreter

 - full asyncio http server also does not work, as only first request works, then crawlee
   complains that not all async tasks have been completed.
   No joke, asyncio http server has not completed, therefore it cannot work together

Therefore crawlee is called from a separate script. We cut off crawlee.
"""

import argparse
import sys
import os
from datetime import timedelta
import json
import webtools
import traceback

os.environ["CRAWLEE_STORAGE_DIR"] = "./storage/{}".format(os.getpid())


crawlee_feataure_enabled = True
try:
    import asyncio

    # https://github.com/apify/crawlee-python
    # https://crawlee.dev/python/api
    from crawlee.beautifulsoup_crawler import (
        BeautifulSoupCrawler,
        BeautifulSoupCrawlingContext,
    )
    from crawlee.basic_crawler import BasicCrawler
    from crawlee.basic_crawler.types import BasicCrawlingContext
    from crawlee.playwright_crawler import PlaywrightCrawler, PlaywrightCrawlingContext
except Exception as E:
    print(str(E))
    crawlee_feataure_enabled = False


async def main() -> None:
    webtools.WebConfig.use_print_logging() 

    parser = webtools.ScriptCrawlerParser()
    parser.parse()
    if not parser.is_valid():
        sys.exit(1)
        return

    if not crawlee_feataure_enabled:
        print("Python: crawlee package is not available")
        sys.exit(1)
        return

    request = parser.get_request()
    print("Running request:{}".format(request))

    crawler = PlaywrightCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=10,
        request_handler_timeout=timedelta(seconds=request.timeout_s),
    )

    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        print(f"Processing {context.request.url} ...")

        response = webtools.PageResponseObject(request.url)
        interface = webtools.ScriptCrawlerInterface(parser, request)

        try:
            # maybe we could send header information that we accept text/rss

            headers = {}
            for item in context.response.headers:
                headers[item] = context.response.headers[item]

            response.url = context.request.loaded_url
            response.request_url = request.url

            # result['loaded_url'] = context.page.url
            response.status_code = context.response.status
            response.headers = headers

            if request.ping:
                interface.response = response
                interface.save_response()
                return

            if response.get_content_length() > webtools.PAGE_TOO_BIG_BYTES:
                response.status_code = 500
                interface.response = response
                interface.save_response()
                print("Response too big")
                return

            content_type = response.get_content_type()
            if content_type and not response.is_content_type_supported():
                response.status_code = webtools.HTTP_STATUS_CODE_PAGE_UNSUPPORTED
                interface.response = response
                interface.save_response()
                print("Content not supported")
                return

            response.set_text(await context.page.content())

            interface.response = response
            interface.save_response()

            print(f"Processing {context.request.url} ...DONE")
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            print(error_text)

            response.status_code = 500
            interface.response = response
            interface.save_response()

    # Run the crawler with the initial list of URLs.
    await crawler.run([parser.args.url])


if __name__ == "__main__":
    asyncio.run(main())