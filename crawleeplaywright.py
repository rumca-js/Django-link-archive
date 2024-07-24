"""
We could use 
https://realpython.com/python-sockets/   "Sending an Application Message"
"""

import argparse
from datetime import timedelta
import json
import rsshistory.webtools

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


class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--url", help="Directory to be scanned")
        self.parser.add_argument("--timeout", help="Timeout expressed in seconds")
        self.parser.add_argument("--ping", help="Ping only")
        self.parser.add_argument("-o", "--output-file", help="Output file")

        self.args = self.parser.parse_args()


async def main() -> None:
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

    crawler = PlaywrightCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=10,
        request_handler_timeout = timedelta(seconds = 10),
    )

    async def save_error(response):
        response.status_code = 500
        all_bytes = response.to_bytes()
        with open(parser.args.output_file, "wb") as fh:
            fh.write(all_bytes)

    async def save_response(response):
        all_bytes = response.to_bytes()
        with open(parser.args.output_file, "wb") as fh:
            fh.write(all_bytes)

    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: PlaywrightCrawlingContext) -> None:
        print(f'Processing {context.request.url} ...')

        try:
            result = {}
            # maybe we could send header information that we accept text/rss
            result['url'] = context.request.url
            result['loaded_url'] = context.request.loaded_url
            result['status_code'] = context.response.status

            headers = {}
            for item in context.response.headers:
                headers[item] = context.response.headers[item]
            result['headers'] = headers

            response = rsshistory.webtools.PageResponseObject(result['url'], headers = result['headers'])

            if parser.args.ping:
                await save_response(response)
                return

            if response.get_content_length() > PAGE_TOO_BIG_BYTES:
                await save_error(response)
                print("Response too big")
                return

            content_type = response.get_content_type()
            if content_type and not response.is_content_type_supported():
                await save_error(response)
                print("Content not supported")
                return

            # result['loaded_url'] = context.page.url
            result['page_content'] = await context.page.content()

            response.content = result['page_content']

            await save_response(response)

            print(f'Processing {context.request.url} ...DONE')
        except Exception as E:
            print("Exception:{}".format(str(E)))

            response = rsshistory.webtools.PageResponseObject(result['url'])
            await save_error(response)


    # Run the crawler with the initial list of URLs.
    await crawler.run([parser.args.url])


if __name__ == '__main__':
    asyncio.run(main())
