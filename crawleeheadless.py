"""
We could use 
https://realpython.com/python-sockets/   "Sending an Application Message"
"""

import argparse
from datetime import timedelta
import json
import rsshistory.ipc

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
    p = Parser()
    p.parse()
    print("Parsing")

    if "url" not in p.args:
        print("Url file not in args")
        return

    if "output_file" not in p.args:
        print("Output file not in args")
        return

    if p.args.url is None:
        print("Url file not in args")
        return

    if p.args.output_file is None:
        print("Output file not in args")
        return

    print("Cralwer")
    print(p.args.output_file)

    crawler = BeautifulSoupCrawler(
        # Limit the crawl to max requests. Remove or increase it for crawling all links.
        max_requests_per_crawl=10,
        request_handler_timeout = timedelta(seconds = 10),
    )

    async def save_error(response):
        response.status_code = 500
        all_bytes = response.to_bytes()
        with open(p.args.output_file, "wb") as fh:
            fh.write(all_bytes)

    # Define the default request handler, which will be called for every request.
    @crawler.router.default_handler
    async def request_handler(context: BeautifulSoupCrawlingContext) -> None:
        print(f'Processing {context.request.url} ...')

        try:
            result = {}
            # maybe we could send header information that we accept text/rss

            result['url'] = context.request.url
            result['loaded_url'] = context.request.loaded_url
            result['status_code'] = context.http_response.status_code

            headers = {}
            for item in context.http_response.headers:
                headers[item] = context.http_response.headers[item]
            result['headers'] = headers

            response = rsshistory.ipc.PageResponseObject(result['url'], headers = result['headers'])
            if response.get_content_length() > PAGE_TOO_BIG_BYTES:
                await save_error(response)
                print("Response too big")
                return

            content_type = response.get_content_type()
            if content_type and not response.is_content_type_supported():
                await save_error(response)
                print("Content not supported")
                return

            # todo check in headers if we accept payload
            result['page_content'] = str(context.soup)

            response.content = result['page_content']

            all_bytes = response.to_bytes()
            with open(p.args.output_file, "wb") as fh:
                fh.write(all_bytes)
        except Exception as E:
            print("Exception:{}".format(str(E)))

            response = rsshistory.ipc.PageResponseObject(result['url'])
            await save_error(response)


    # Run the crawler with the initial list of URLs.
    await crawler.run([p.args.url])


if __name__ == '__main__':
    asyncio.run(main())
