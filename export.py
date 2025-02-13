"""
This program uses API key from webpage, and uses it to produce static lists
Might be slow.

./data/export/static_lists/

 -api API key
 -search "search term"
"""

import argparse
import json
from pathlib import Path

from rsshistory.webtools import (
    Url,
    WebConfig,
)


export_dir = Path("..") / "data" / "exports" / "static_lists"


class Exporter(object):
    def __init__(self, file_name):
        self.file_name = file_name
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def close(self):
        json_data = {"entries" : self.entries }
        text = json.dumps(json_data, indent=4)

        if self.file_name:
            export_dir.mkdir(parents=True, exist_ok=True)
            file_name = export_dir / self.file_name
            with open(str(file_name), "w") as fh:
                fh.write(text)
        else:
            print(text)

        return text


class Processor(object):
    def __init__(self, parser, args):
        self.parser = parser
        self.args = args
        self.exporter = Exporter(args.file_name)
        self.num_pages = None

    def process(self):
        page_num = 1

        if self.args.page_limit:
            self.num_pages = int(self.args.page_limit)

        while True:
            if self.num_pages and page_num > self.num_pages:
                break

            if not self.num_pages or page_num <= self.num_pages:
                status = self.process_for_page(page_num)
                print("Done page [{}/{}]".format(page_num, self.num_pages))

                if not status:
                    break
            else:
                break

            page_num += 1

        self.exporter.close()

    def process_for_page(self, page_num):
        address = self.args.host
        workspace = self.args.workspace
        search_term = self.args.search
        key = self.args.key

        full_address = f"https://{address}/apps/{workspace}/entries-json/?tags=1&search={search_term}&page={page_num}&key={key}"
        print(f"Fetching {full_address}")
        u = Url(full_address)
        u.options.ssl_verify = False

        response = u.get_response()
        if response.is_valid():
            json = self.response_to_json(response)
            if not self.are_entries(json):
                return False

            if self.num_pages == None:
                self.num_pages = int(json["num_pages"])

            self.process_json_entries(json["entries"])

            return True
        else:
            print(response)
            return False

    def process_json_entries(self, entries):
        for entry in entries:
            self.exporter.add_entry(entry)

    def are_entries(self, json):
        if not json or "entries" not in json or len(json["entries"]) == 0:
            return False

        return True

    def response_to_json(self, response):
        object = json.loads(response.get_text())
        return object


def parse():
    parser = argparse.ArgumentParser(prog="Exporter", description="Workspace Exporter")

    parser.add_argument("-s", "--search")
    parser.add_argument("-k", "--key")
    parser.add_argument("-f", "--file-name")
    parser.add_argument("--page-limit")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("-w", "--workspace")

    return parser, parser.parse_args()


def main():
    WebConfig.init()
    WebConfig.disable_ssl_warnings()

    parser, args = parse()

    p = Processor(parser, args)
    p.process()


if __name__ == "__main__":
    main()
