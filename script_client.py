"""
Script that can be used for debuggin server, checking connection
"""
import socket
import argparse
import json
from datetime import datetime, timedelta

from rsshistory.webtools import ipc, PageRequestObject, get_request_to_bytes


max_transaction_timeout_s = 40




def process_url(c, url):

    script = "poetry run python crawleebeautifulsoup.py"
    request = PageRequestObject(url)
    request.timeout_s = 30

    bytes = get_request_to_bytes(request, script)
    c.send(bytes)

    #c.send_command_string("commands.debug", "15")

    #c.send_command_string("PageRequestObject.__init__", "OK")
    #c.send_command_string("PageRequestObject.url", url)
    #c.send_command_string("PageRequestObject.timeout", "15")
    #c.send_command_string(
    #    "PageRequestObject.script", 
    #)
    #c.send_command_string("PageRequestObject.__del__", "OK")

    print("Sent request correctly")

    time_start = datetime.now()

    while True:
        command_data = c.get_command_and_data()
        if command_data:
            # response

            if command_data[0] == "PageResponseObject.__init__":
                pass
            elif command_data[0] == "PageResponseObject.url":
                print("Received url:{}".format(command_data[1].decode()))
            elif command_data[0] == "PageResponseObject.headers":
                print("Received headers:{}".format(command_data[1].decode()))
            elif command_data[0] == "PageResponseObject.status_code":
                print("Received status_code:{}".format(command_data[1].decode()))
            elif command_data[0] == "PageResponseObject.text":
                print("Received page_content")
            elif command_data[0] == "PageResponseObject.request_url":
                print("Received request url:{}".format(command_data[1].decode()))
            elif command_data[0] == "PageResponseObject.__del__":
                c.send_command_string("commands.close", "OK")
                break

            # other commands

            elif command_data[0] == "debug.requests":
                print("Requests len:{}".format(command_data[1].decode()))

            else:
                print("Unsupported command:{}".format(command_data[0]))
                break

        if c.is_closed():
            break

        # normal scenario - there is no command from server

        diff = datetime.now() - time_start

        if diff.total_seconds() > max_transaction_timeout_s:
            print("Could not obtain data in time limit")
            c.close()
            break

    c.close()


def client_program(parser):
    if "port" in parser.args and parser.args.port:
        port = parser.args.port
    else:
        port = ipc.DEFAULT_PORT

    c = ipc.SocketConnection()
    if not c.connect(ipc.SocketConnection.gethostname(), port):
        print(f"Cannot connect to host at port {port}")
        return
    else:
        print(f"Connected to host at port {port} {c}")

    message = ""
    while message.lower().strip() != "bye":
        message = input(" -> ")

        try:
            process_url(c, message)
        except Exception as E:
            print("Exception:{}".format(str(E)))
            c.close()
            return

    c.close()


class Parser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Script server")
        self.parser.add_argument("--port", type=int, help="Port")
        self.parser.add_argument("-o", "--output-file", help="Response binary file")

        self.args = self.parser.parse_args()

    def is_valid(self):
        return True


if __name__ == "__main__":
    p = Parser()
    p.parse()

    client_program(p)
    # data = bytes.decode(errors="ignore")  # receive response
