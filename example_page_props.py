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
)


__version__ = "0.0.1"


def show_page_details(url, verbose=False):
    options = Url.get_url_options(url)

    #options.use_headless_browser = True
    #options.use_full_browser = True
    #options.user_browser_promotions = False

    u = Url(url, page_options = options)
    u.get_response()

    print("Handler:{}".format(type(u.get_handler())))
    print("Title:{}".format(u.get_title()))
    print("Description:{}".format(u.get_description()))
    print("Language:{}".format(u.get_language()))
    print("Author:{}".format(u.get_author()))
    print("Album:{}".format(u.get_album()))

    handler = u.get_handler()
    if type(handler) is HttpPageHandler:

        response = handler.get_response()
        print("Response is valid?:{}".format(u.get_response().is_valid()))
        print("Status code:{}".format(response.status_code))
        print("Content-Type:{}".format(response.get_content_type()))
        print("Charset:{}".format(response.get_content_type_charset()))

        if type(handler.p) is RssPage:
            print("Feed title:{}".format(handler.p.feed.feed.title))
            print("Feed description:{}".format(handler.p.feed.feed.description))
            print("Feed published:{}".format(handler.p.feed.feed.published))

            index = 0
            for entry in handler.p.feed.entries:
                if index == 0:
                    print("Feed Entry Link:{}".format(entry.link))
                    print("Feed Entry Title:{}".format(entry.title))
                index += 1

            print("Feed Entries:{}".format(index))

            index = 0
            for entry in handler.p.get_entries():
                if index == 0:
                    print("Entry Link:{}".format(entry["link"]))
                    print("Entry Title:{}".format(entry["title"]))
                index += 1
            print("Entries:{}".format(index))
        if type(handler.p) is HtmlPage:
            print("meta title:{}".format(handler.p.get_meta_field("title")))
            print("meta description:{}".format(handler.p.get_meta_field("description")))
            print("meta keywords:{}".format(handler.p.get_meta_field("keywords")))

            print("og:title:{}".format(handler.p.get_og_field("title")))
            print("og:description:{}".format(handler.p.get_og_field("description")))
            print("og:image:{}".format(handler.p.get_og_field("image")))
            print("og:site_name:{}".format(handler.p.get_og_field("site_name")))

            print("schema image:{}".format(handler.p.get_schema_field("thumbnailUrl")))

            rss_u = Url.find_rss_url(url)
            if rss_u:
                print("RSS url:{}".format(rss_u.url))

    if u.get_contents():
        if verbose:
            print(u.get_contents())
        else:
            print("Contents?:Yes")
    else:
        print("Contents?:No")


async def main():
    WebConfig.use_print_logging()

    # TODO - there seems to be some problems with feedparser, when used with asyncio threads
    # module 'xml.sax.expatreader' has no attribute 'create_parser'

    url = input("Insert URL to check:")
    show_page_details(url)


if __name__ == "__main__":
    start_time = time.time()
    asyncio.run(main())
    print(f"Done in {time.time() - start_time} seconds")
