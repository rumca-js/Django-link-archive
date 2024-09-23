"""
This server accepts web scraping commands.

We communicate through binary interface:
 - PageRequestObject
 - PageResponseObject

Communication through port should be used, communication through single file is a potential bottleneck

Communication is only for request - response pairs.

Communication breakdown:
    [server] Server starts, listens for incoming clients
    [client A] client connects
    [server] Accepts client. Handles connection in in task 1
    [client A] client sends request
    [server] Start crawling script in task 1
    [server] we end processing in task 1
    [crawling script] starts, fetches internet data produces response, connects to server
    [server] Accepts crawling script client. Handles connection in in task 2
    [crawling script] crawling script sends response
    [crawling script] terminates
    [server] Handles response in task 2
    [server] Closes all client sockets for that request
    [server] Closes socket for crawling script
    [server] we end processing in task 2
    [client A] terminates
"""

import argparse
import socket
import threading
import json
import shutil

from pathlib import Path
from rsshistory.webtools import ScrapingServer, ScrapingServerParser, WebConfig
import subprocess
import traceback
from datetime import datetime, timedelta


if __name__ == "__main__":
    WebConfig.init()

    if WebConfig.script_responses_directory is not None:
        path = Path(WebConfig.script_responses_directory)
        if path.exists():
            shutil.rmtree(str(path), ignore_errors=True, onerror=None)

    p = ScrapingServerParser()
    p.parse()

    server = ScrapingServer(p.host, p.port)
    server.serve_forever()
