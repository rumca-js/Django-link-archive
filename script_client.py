"""
Script that can be used for debuggin server, checking connection
"""
import socket
import argparse
import json

from rsshistory import ipc


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
        print(f"Connect to host at port {port}")

    message = ""
    while message.lower().strip() != 'bye':
        message = input(" -> ")

        c.send_command_string("PageRequestObject.__init__", "OK")
        c.send_command_string("PageRequestObject.url", message)
        c.send_command_string("PageRequestObject.timeout", "15")
        c.send_command_string("PageRequestObject.script", "poetry run python crawleebeautifulsoup.py")
        c.send_command_string("PageRequestObject.__del__", "OK")

        while True:
            command_data = c.get_command_and_data()
            if command_data:
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
                elif command_data[0] == "PageResponseObject.__del__":
                    return
                elif command_data[0] == "PageResponseObject.request_url":
                    print("Received request url:{}".format(command_data[1].decode()))
                else:
                    print("Unsupported command:{}".format(command_data[0]))
                    break

            if c.closed:
                print("Closed")
                return
            # normal scenario - there is no command from server

        if c.closed:
            print("Closed")
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


if __name__ == '__main__':
    p = Parser()
    p.parse()

    client_program(p)
    # data = bytes.decode(errors="ignore")  # receive response
