import argparse
import json

from rsshistory import webtools
from rsshistory import ipc


class Parser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--url", help="Directory to be scanned")
        self.parser.add_argument("--timeout",default=10, type=int, help="Timeout expressed in seconds")
        self.parser.add_argument("--ping", default=False, help="Ping only")
        self.parser.add_argument("--port", type=int, help="Port")
        self.parser.add_argument("--ssl-verify", default=False, help="SSL verify")

        # TODO implement
        self.parser.add_argument("--input-data", help="Input request file")

        self.parser.add_argument("-i", "--input", help="Requests binary file")
        self.parser.add_argument("-o", "--output-file", help="Response binary file")

        self.args = self.parser.parse_args()

    def is_valid(self):
        if "url" not in self.args:
            print("Url file not in args")
            return False

        if "output_file" not in self.args:
            print("Output file not in args")
            return False

        if self.args.url is None:
            print("Url file not in args")
            return False

        if self.args.output_file is None and self.args.port is None:
            print("Output file and port not in args")
            return False

        return True

    def get_request(self):
        r = webtools.PageRequestObject(self.args.url)
        r.timeout_s = self.args.timeout
        r.ping = self.args.ping

        return r


class ScriptCrawlerInterface(object):
    """
    Interface that can be inherited by any browser, browser engine, crawler
    """
    def __init__(self, parser, request):
        self.parser = parser
        self.request = request
        self.response = None

    def run(self):
        """
        Should use request to produce response
        @return response
        """
        return

    def save_response(self):
        all_bytes = bytearray()

        # same as PageResponseObject
        bytes1 = ipc.string_to_command("PageResponseObject.__init__", "OK")
        bytes2 = ipc.string_to_command("PageResponseObject.url", self.response.url)
        bytes3 = ipc.string_to_command("PageResponseObject.request_url", self.response.request_url)
        bytes4 = ipc.string_to_command("PageResponseObject.status_code", str(self.response.status_code))
        bytes5 = ipc.string_to_command("PageResponseObject.text", self.response.text)
        bytes6 = ipc.string_to_command("PageResponseObject.headers", json.dumps(self.response.headers))
        bytes7 = ipc.string_to_command("PageResponseObject.__del__", "OK")

        all_bytes.extend(bytes1)
        all_bytes.extend(bytes2)
        all_bytes.extend(bytes3)
        all_bytes.extend(bytes4)
        all_bytes.extend(bytes5)
        all_bytes.extend(bytes6)
        all_bytes.extend(bytes7)

        if self.parser.args.output_file:
            with open(self.parser.args.output_file, "wb") as fh:
                fh.write(all_bytes)

        if self.parser.args.port:
            con = ipc.SocketConnection()
            con.connect(ipc.SocketConnection.gethostname(), self.parser.args.port)
            con.send(all_bytes)
