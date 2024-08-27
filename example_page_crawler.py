"""
Simple scraping script.

 - reads site map, reads links
 - follows each link t read more links
 - etc. etc.
"""
import socket
import json
import traceback

from webtools import (
   PageOptions,
   WebConfig,
   WebLogger,
   DomainCache,
   Url,
   HttpPageHandler,
   ContentLinkParser,
   run_server_task,
)


__version__ = "0.0.1"


class Crawler(object):

    pages = {}

    def crawl(self, url):
        domain_cache = DomainCache.get_object(url)
        self.add(domain_cache.url)

        site_maps_urls = domain_cache.get_site_maps_urls()
        for site_map_url in site_maps_urls:
            self.add(site_map_url)

        self.add(url)

        while self.process_urls():
            pass

    def add(self, url):
        if url not in Crawler.pages:
            print("Added:{}".format(url))
            Crawler.pages[url] = {}

    def process_urls(self):
        url = self.get_next_to_crawl()
        if url:
            response = self.process_url(url)
            if response and response.is_valid():
                text = response.get_text()
                if text:
                    parser = ContentLinkParser(url, text)
                    links = parser.get_links()
                    for link in links:
                        self.add(link)

            Crawler.pages[url]["response"] = response
            return True

        return False

    def get_next_to_crawl(self):
        for url in Crawler.pages:
            page_data = Crawler.pages[url]
            if len(page_data) == 0:
                return url

    def process_url(self, url):
        print("Scraping:{}".format(url))

        options = PageOptions()
        options.use_headless_browser = False
        options.use_full_browser = False

        url = Url(url = url, page_options = options)
        handler = url.get_handler()
        response = url.get_response()
        return response


def main():
    WebConfig.use_print_logging()

    # more advanced processing is possible through other frameworks
    server = run_server_task()

    HttpPageHandler.crawling_server_port = server.port
    HttpPageHandler.crawling_full_script = "poetry run python crawleebeautifulsoup.py"
    HttpPageHandler.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"

    print("Enter page to crawl")
    url = input("->")

    c = Crawler()
    c.crawl(url)


if __name__ == "__main__":
    main()
