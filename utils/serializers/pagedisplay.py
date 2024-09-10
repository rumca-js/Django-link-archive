import argparse

from webtools import (
    Url,
    RssPage,
    HtmlPage,
    WebConfig,
    HttpPageHandler,
)
from utils.services import OpenRss


class PageDisplay(object):
    def __init__(self, url, verbose=False, method=None):
        options = Url.get_url_options(url)

        if method == "headless":
            options.use_headless_browser = True
            options.use_browser_promotions = False
        if method == "full":
            options.use_full_browser = True
            options.use_browser_promotions = False

        u = Url(url, page_options=options)
        u.get_response()

        print("Handler:{}".format(type(u.get_handler())))
        print("Title:{}".format(u.get_title()))
        print("Description:{}".format(u.get_description()))
        print("Language:{}".format(u.get_language()))
        print("Author:{}".format(u.get_author()))
        print("Album:{}".format(u.get_album()))

        print("RSS path:{}".format(Url.find_rss_url(u)))

        feeds = u.get_feeds()
        for feed in feeds:
            print("Feed URL:{}".format(feed))

        if not feeds or len(feeds) == 0:
            rss = OpenRss(url)
            link = rss.find_rss_link()
            if link:
                print("Feed URL:{}".format(link))

        handler = u.get_handler()
        if type(handler) is HttpPageHandler:
            response = handler.get_response()
            print("Response is valid?:{}".format(u.get_response().is_valid()))
            print("Status code:{}".format(response.status_code))
            print("Content-Type:{}".format(response.get_content_type()))
            print("Charset:{}".format(response.get_content_type_charset()))
            print("Page type:{}".format(type(handler.p)))

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
                for entry in handler.get_entries():
                    if index == 0:
                        print("Entry Link:{}".format(entry["link"]))
                        print("Entry Title:{}".format(entry["title"]))
                    index += 1
                print("Entries:{}".format(index))
            if type(handler.p) is HtmlPage:
                print("meta title:{}".format(handler.p.get_meta_field("title")))
                print(
                    "meta description:{}".format(
                        handler.p.get_meta_field("description")
                    )
                )
                print("meta keywords:{}".format(handler.p.get_meta_field("keywords")))

                print("og:title:{}".format(handler.p.get_og_field("title")))
                print("og:description:{}".format(handler.p.get_og_field("description")))
                print("og:image:{}".format(handler.p.get_og_field("image")))
                print("og:site_name:{}".format(handler.p.get_og_field("site_name")))

                print(
                    "schema image:{}".format(handler.p.get_schema_field("thumbnailUrl"))
                )

        elif type(handler) is Url.youtube_channel_handler:
            index = 0
            for entry in handler.get_entries():
                if index == 0:
                    print("Entry Link:{}".format(entry["link"]))
                    print("Entry Title:{}".format(entry["title"]))
                index += 1
            print("Entries:{}".format(index))

        if u.get_contents():
            if verbose:
                print(u.get_contents())
            else:
                print("Contents?:Yes")
        else:
            print("Contents?:No")


class PageDisplayParser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Page properties")
        self.parser.add_argument(
            "--timeout", default=10, type=int, help="Timeout expressed in seconds"
        )
        self.parser.add_argument(
            "--port", type=int, default=0, help="Port, if using web scraping server"
        )
        self.parser.add_argument("--method", help="method. Choices: full, headless")
        self.parser.add_argument("--url", help="Url to fetch")
        self.parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")

        self.args = self.parser.parse_args()
