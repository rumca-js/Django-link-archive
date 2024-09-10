"""
Script that can be used for debuggin server, checking connection
"""
import socket
import argparse
import json
from datetime import datetime, timedelta

from webtools import ipc, ScrapingClient, ScrapingClientParser, WebConfig


def main():
    WebConfig.init()

    p = ScrapingClientParser()
    p.parse()

    c = ScrapingClient(p.host, p.port)
    c.set_scraping_script("poetry run python crawleebeautifulsoup.py")
    if not c.connect():
        print("Could not connect")
        return

    message = ""
    while message.lower().strip() != "exit":
        message = input(" -> ")
        response = c.send_request_for_url(message)

        print("Received response:{}".format(response))

        if c.is_closed():
            print("Client has closed")
            return


if __name__ == "__main__":
    main()
