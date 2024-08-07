"""
I wanted to use crawlee with socket server
  - there are problems with running crawlee in any project
  - I have been using asyncio,

  - on windows such system works
  - on linux raspberry it does not. Asyncio does not allow to define new loop from task
    set_wakeup_fd only works in main thread of the main interpreter

  - full asyncio http server also does not work, as only first request works, then crawlee
    complains that not all async tasks have been completed.
    No joke, asyncio http server has not completed, therefore it cannot work together

The effect is that it easier just to call script, which always works.
"""

import argparse
import sys
from datetime import timedelta
import json
from rsshistory import webtools
import crawlerscript
import traceback


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
    parser = crawlerscript.Parser()
    parser.parse()
    if not parser.is_valid():
        return

    request = parser.get_request()
    print("Running request:{}".format(request))

    crawler = BeautifulSoupCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=10,
        request_handler_timeout=timedelta(seconds=request.timeout_s),
        retry_on_blocked = False,
        max_session_rotations = 2,
    )
    
    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        print(f"Processing {context.request.url} ...")

        response = webtools.PageResponseObject(request.url)
        try:
            # maybe we could send header information that we accept text/rss

            headers = {}
            for item in context.http_response.headers:
                headers[item] = context.http_response.headers[item]

            # result['url'] = context.request.url
            # result['loaded_url'] = context.request.loaded_url
            response.url = context.request.loaded_url
            response.request_url = request.url
            response.status_code = context.http_response.status_code
            response.headers = headers

            if request.ping:
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                c.response = response
                c.save_response()
                return

            if response.get_content_length() > webtools.PAGE_TOO_BIG_BYTES:
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                response.status_code = 500
                c.response = response
                c.save_response()
                print("Response too big")
                return

            content_type = response.get_content_type()
            if content_type and not response.is_content_type_supported():
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                response.status_code = webtools.HTTP_STATUS_CODE_PAGE_UNSUPPORTED
                c.response = response
                c.save_response()
                print("Content not supported")
                return

            response.set_text(str(context.soup))

            c = crawlerscript.ScriptCrawlerInterface(parser, None)
            c.response = response
            c.save_response()

            print(f"Processing {context.request.url} ...DONE")
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            print(error_text)

            c = crawlerscript.ScriptCrawlerInterface(parser, None)
            response.status_code = 500
            c.response = response
            c.save_response()

            sys.exit(1)

    try:
        # Run the crawler with the initial list of URLs.
        await crawler.run([parser.args.url])
    except Exception as E:
        print(str(E))
        error_text = traceback.format_exc()
        print(error_text)


if __name__ == "__main__":
    asyncio.run(main())
