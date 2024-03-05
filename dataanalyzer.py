"""
usage: dataanalyzer.py [-h] [--dir DIR] [--count] [--summary] [--find-tag find_tag] [--find find] [--find-tags] [-i]
                       [-v VERBOSITY]

Data analyzer program

optional arguments:
  -h, --help            show this help message and exit
  --dir DIR             Directory path
  --count               Counts entries
  --summary             Displays summary
  --find-tag find_tag   Find entries with a specific tag
  --find find           Find entries with text
  --find-tags           Find all available tags
  -i, --ignore-case     Ignores case
  -v VERBOSITY, --verbosity VERBOSITY
                        Verbosity level

TODO
 - datanalayze --source-url hackernews = search from particular source
 - Output in md file?
 - Maybe it could produce a chart?
"""
import argparse
import os
import json


def get_list_files(directory):
    file_list = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            file_list.append(os.path.join(root, file))
    return file_list

def read_file_contents(file_path):
    with open(file_path, "r") as f:
        return f.read()


class MainObject(object):
    def __init__(self, parser):
        self.parser = parser
        self.files = get_list_files(self.parser.dir)
        self.result = None

    def process(self):
        if self.is_entry_search():
            count = self.find_entries()
            if self.parser.args.summary:
                print("Finished with count:{}".format(count))
        elif self.parser.args.find_tags:
            count = self.find_tags()
        else:
            print("No condition to search")

    def find_entries(self):
        result_count = 0

        if self.parser.args.summary:
            print("Entering dir:{}".format(self.parser.dir))

        for afile in self.files:
            if not afile.endswith(".json"):
                continue

            entries = self.read_file(afile)
            if not entries:
                continue

            for entry in entries:
                if self.is_entry_found(entry):
                    self.print_entry(entry)
                    result_count += 1

        if self.parser.args.summary:
            print("Leaving dir:{}".format(self.parser.dir))

        return result_count

    def print_entry(self, entry):
        level = "1"
        if self.parser.args.verbosity:
            level = self.parser.args.verbosity

        if level == "1":
            print("{}".format(entry["link"]))
        elif level == "2":
            description = ""
            if "description" in entry:
                description = entry["description"]
            print("{}\n{}".format(entry["link"], description))
        elif level == "0":
            pass
        else:
            print("{}".format(entry["link"]))

    def is_entry_found(self, entry):
        text = None

        if self.parser.args.find:
            text = self.parser.args.find
        elif self.parser.args.find_tag:
            text = self.parser.args.find_tag

        elements = []
        if self.parser.args.find:
            elements.extend(self.get_searchable_fields())
        elif self.parser.args.find_tag:
            eleemnts.append("tags")
        else:
            print("Cannot find condition to find")
            return

        ignore_case = False
        if self.parser.args.ignore_case:
            ignore_case = self.parser.args.ignore_case

        for element in elements:
            if element == "tags":
                if "tags" in entry and text in entry["tags"]:
                    if "link" in entry:
                        return entry
            if element == "title" or element == "description" or element == "link":
                if element in entry:
                    entry_text = entry[element]

                    if not entry_text:
                        continue

                    if ignore_case:
                        if entry_text.lower().find(text.lower()) >= 0:
                            if "link" in entry:
                                return entry
                    else:
                        if entry_text.find(text) >= 0:
                            if "link" in entry:
                                return entry

    def find_tags(self):
        tags = {}
        for afile in self.files:
            if not afile.endswith(".json"):
                continue

            items = self.read_file(afile)
            if not items:
                continue

            for item in items:
                if "tags" in item and len(item["tags"]) > 0:
                    for tag in item["tags"]:
                        if tag in tags:
                            tags[tag] += 1
                        else:
                            tags[tag] = 1

        for tag in tags:
            print("Tag:{} Count:{}".format(tag, tags[tag]))

    def is_entry_search(self):
        if self.parser.args.find_tag:
            return True
        if self.parser.args.find:
            return True

    def read_file(self, afile):
        text = read_file_contents(afile)

        try:
            j = json.loads(text)

            if "links" in j:
                return j["links"]
            if "sources" in j:
                return j["sources"]

            return j
        except Exception as E:
            print("Could not read file: {}".format(afile))

    def get_searchable_fields(self):
        return [
                "title",
                "link",
                "description",
                "tags",
                ]


class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--dir", help="Directory to be scanned")
        self.parser.add_argument("--count", action="store_true", help="Counts entries")
        self.parser.add_argument("--summary", action="store_true", help="Displays summary at the end")
        self.parser.add_argument("--find-tag", metavar="find_tag", help="Find entries with a specific tag")
        self.parser.add_argument("--find", metavar="find", help="Find entries with text")
        self.parser.add_argument("--find-tags", action="store_true", help="Find all available tags")
        self.parser.add_argument("-i", "--ignore-case", action="store_true", help="Ignores case")
        self.parser.add_argument("-v", "--verbosity", help="Verbosity level")
        
        self.args = self.parser.parse_args()

        if self.args.dir:
            self.dir = self.args.dir


def main():
    p = Parser()
    p.parse()

    m = MainObject(p)
    m.process()


if __name__ == "__main__":
    main()
