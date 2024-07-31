"""
Script that can be used for debuggin server, checking connection
"""
import socket
import json
import traceback

from rsshistory.webtools import RequestBuilder, PageOptions, WebLogger
from rsshistory import ipc


class ClientWebLogger(object):
    def info(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def debug(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def warning(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def error(info_text, detail_text="", user=None, stack=False):
        print(info_text)
        print(detail_text)

    def notify(info_text, detail_text="", user=None):
        print(info_text)
        print(detail_text)

    def exc(exception_object, info_text=None, user=None):
        print(str(exception_object))

        error_text = traceback.format_exc()
        print("Exception format")
        print(error_text)

        stack_lines = traceback.format_stack()
        stack_string = "".join(stack_lines)
        print("Stack:")
        print("".join(stack_lines))


def test_requests():
    print("Test requests")
    RequestBuilder.crawling_server_port = 0
    RequestBuilder.crawling_headless_script = None

    options = PageOptions()

    b = RequestBuilder(url="https://google.com", options=options)

    response = b.get_response()

    print(f"Response:{response}")


def test_headless():
    print("Test headless")
    RequestBuilder.crawling_server_port = ipc.DEFAULT_PORT
    RequestBuilder.crawling_headless_script = "poetry run python crawleebeautifulsoup.py"

    options = PageOptions()
    options.use_headless_browser = True

    b = RequestBuilder(url="https://google.com", options=options)

    response = b.get_response()

    print(f"Response:{response}")


def test_full():
    print("Test full")
    RequestBuilder.crawling_server_port = ipc.DEFAULT_PORT
    RequestBuilder.crawling_full_script = "poetry run python crawleebeautifulsoup.py"

    options = PageOptions()
    options.use_full_browser = True

    b = RequestBuilder(url="https://google.com", options=options)

    response = b.get_response()

    print(f"Response:{response}")


def client_program():
    WebLogger.web_logger = ClientWebLogger

    test_requests()
    test_headless()
    test_full()


if __name__ == '__main__':
    client_program()
    # data = bytes.decode(errors="ignore")  # receive response
