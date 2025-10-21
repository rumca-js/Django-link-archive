"""
TODO
these scripts will not work in case of multithreaded app
"""

import os
import psutil
from pathlib import Path

from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from .webtoolsx import WebLogger


class WebConfig(object):
    """
    API to configure webtools
    """

    def use_logger(Logger):
        WebLogger.web_logger = Logger

    def use_print_logging():
        from utils.logger import PrintLogger

        WebLogger.web_logger = PrintLogger()

    def disable_ssl_warnings():
        disable_warnings(InsecureRequestWarning)
