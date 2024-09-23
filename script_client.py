"""
Script that can be used for debuggin server, checking connection
"""
import socket
import argparse
import json
from datetime import datetime, timedelta

from rsshistory.webtools import ScrapingClient, ScrapingClientParser, WebConfig


def main():
    WebConfig.init()

    p = ScrapingClientParser()
    p.parse()

    c = ScrapingClient(p.host, p.port)
    c.set_scraping_script("poetry run python crawleebeautifulsoup.py")
    if not c.connect():
        print("Could not connect")
        return

    c.serve_forever()


if __name__ == "__main__":
    main()
