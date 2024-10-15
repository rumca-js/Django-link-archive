import argparse

from rsshistory.webtools import (
    Url,
    RssPage,
    HtmlPage,
    WebConfig,
    HttpPageHandler,
)
from utils.services import OpenRss


class PageDisplay(object):
    def __init__(self, url, verbose=False, method=None):
        u = Url(url)
        if method:
            u.options.mode = method
        u.get_response()

        print("Handler:{}".format(type(u.get_handler())))
        print("Title:{}".format(u.get_title()))
        print("Description:{}".format(u.get_description()))
        print("Language:{}".format(u.get_language()))
        print("Author:{}".format(u.get_author()))
        print("Album:{}".format(u.get_album()))
        print("Thumbnail:{}".format(u.get_thumbnail()))

        print("RSS path:{}".format(Url.find_rss_url(u)))

        feeds = u.get_feeds()
        for feed in feeds:
            print("Feed URL:{}".format(feed))

        handler = u.get_handler()
        if type(handler) is HttpPageHandler:
            response = handler.get_response()
            print("Response is valid?:{}".format(u.get_response().is_valid()))
            print("Status code:{}".format(response.status_code))
            print("Content-Type:{}".format(response.get_content_type()))
            print("Charset:{}".format(response.get_content_type_charset()))
            print("Page type:{}".format(type(handler.p)))

            if type(handler.p) is RssPage:
                pass

            if type(handler.p) is HtmlPage:
                if not feeds or len(feeds) == 0:
                    rss = OpenRss(url)
                    link = rss.find_rss_link()
                    if link:
                        print("Feed URL:{}".format(link))

                print("Favicon:{}".format(handler.p.get_favicon()))
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
            pass

        index = 0
        for entry in u.get_entries():
            if index == 0:
                print("Has entries")
                print("Entry Link:{}".format(entry["link"]))
                print("Entry Title:{}".format(entry["title"]))
            index += 1

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
        self.parser.add_argument(
            "-v",
            "--verbose",
            action="store_true",
            help="Verbose. For example: displays full contents",
        )

        self.args = self.parser.parse_args()
