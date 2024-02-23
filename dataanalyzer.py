"""
../data/input/rsshistory/

read all files.
check source url

 - check if corporate, open source, personal

 - source ->
     list of domains in links. (no https?)   (how many times, name, first time date, last updated)
     (links / hour)

     total amount of seconds / total amount of entries

 - token ->
     day -> how many times mentioned (title)
     list of links, with titles

datanalayze --source-url hackernews


dataanalyzer.py --find Google --dir
 - searches in title, descrpition, just as filters

dataanalyzer.py --find-title Google
 - searches in title, descrpition, just as filters

Output in md file

# Maybe it could produce a chart?
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
        if self.parser.args.find_tag:
            count = self.find_tag()
            if self.parser.args.summary:
                print("Finished with count:{}".format(count))
        elif self.parser.args.find_tags:
            count = self.find_tags()

    def find_tag(self):
        result_count = 0
        tag = self.parser.args.find_tag

        if self.parser.args.summary:
            print("Going into dir {} to find tag {}".format(self.parser.dir, tag))

        for afile in self.files:
            if not afile.endswith(".json"):
                continue

            items = self.read_file(afile)
            if not items:
                continue

            for item in items:
                if "tags" in item and tag in item["tags"]:
                    if "link" in item:
                        print("{}".format(item["link"]))
                        result_count += 1

        return result_count

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



class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--dir", help="Directory path")
        self.parser.add_argument("--count", action="store_true", help="Counts entries")
        self.parser.add_argument("--summary", action="store_true", help="Displays summary")
        self.parser.add_argument("--find-tag", metavar="tag", help="Find entries with a specific tag")
        self.parser.add_argument("--find-tags", action="store_true", help="Find entries with a specific tag")
        
        self.args = self.parser.parse_args()

        if self.args.dir:
            self.dir = self.args.dir
        
        """
        if args.dir:
            print("Directory:", args.dir)
        if args.count:
            print("Count option selected")
        if args.find_tag:
            print("Find Tag:", args.find_tag)
        """


def main():
    p = Parser()
    p.parse()

    m = MainObject(p)
    m.process()


if __name__ == "__main__":
    main()
