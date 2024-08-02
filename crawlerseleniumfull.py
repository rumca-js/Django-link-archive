import json
import time
import argparse

from rsshistory import webtools
import crawlerscript


def main():
    parser = crawlerscript.Parser()
    parser.parse()
    if not parser.is_valid():
        return

    request = parser.get_request()

    page = webtools.SeleniumChromeFull(request)
    response = page.get()

    print(f"Processing {parser.args.url} ...DONE")

    i.response = response
    i.save_response()


main()
