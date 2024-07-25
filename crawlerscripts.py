import argparse


class Parser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--url", help="Directory to be scanned")
        self.parser.add_argument("--timeout",default=10, help="Timeout expressed in seconds")
        self.parser.add_argument("--ping", default=False, help="Ping only")

        self.parser.add_argument("-i", "--input", help="Requests binary file")
        self.parser.add_argument("-o", "--output-file", help="Response binary file")

        self.args = self.parser.parse_args()


class ScriptCrawlerInterface(object):
    """
    Interface that can be inherited by any browser, browser engine, crawler
    """
    def __init__(self, parser):
        self.parser = parser

    def run(self):
        return

    def get(self):
        """
        @return PageResponseObject
        """
        return
