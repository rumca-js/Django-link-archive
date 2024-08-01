"""
We could use 
https://realpython.com/python-sockets/   "Sending an Application Message"
"""

import argparse
from datetime import timedelta
import json
from rsshistory import webtools
import crawlerscript
import traceback

PAGE_TOO_BIG_BYTES = 5000000


crawlee_feataure_enabled = True
try:
    import asyncio

    # https://github.com/apify/crawlee-python
    # https://crawlee.dev/python/api
    from crawlee.beautifulsoup_crawler import BeautifulSoupCrawler, BeautifulSoupCrawlingContext
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

    crawler = PlaywrightCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=10,
        request_handler_timeout = timedelta(seconds = request.timeout_s),
    )

    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        print(f'Processing {context.request.url} ...')

        response = webtools.PageResponseObject(request.url)
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
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                c.response = response
                c.save_response()
                return

            if response.get_content_length() > PAGE_TOO_BIG_BYTES:
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                response.status_code = 500
                c.response = response
                c.save_response()
                print("Response too big")
                return

            content_type = response.get_content_type()
            if content_type and not response.is_content_type_supported():
                c = crawlerscript.ScriptCrawlerInterface(parser, None)
                response.status_code = 500
                c.response = response
                c.save_response()
                print("Content not supported")
                return

            response.set_text(await context.page.content())

            c = crawlerscript.ScriptCrawlerInterface(parser, None)
            c.response = response
            c.save_response()

            print(f'Processing {context.request.url} ...DONE')
        except Exception as E:
            print(str(E))
            error_text = traceback.format_exc()
            print(error_text)

            c = crawlerscript.ScriptCrawlerInterface(parser, None)
            response.status_code = 500
            c.response = response
            c.save_response()


    # Run the crawler with the initial list of URLs.
    await crawler.run([parser.args.url])


if __name__ == '__main__':
    asyncio.run(main())
