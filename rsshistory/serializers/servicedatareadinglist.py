import csv
import sys
import io

"""
https://www.tdpain.net/blog/a-year-of-reading
"""

class ReadingList(object):
    def __init__(self, contents=None):
        self.contents = contents

    def get_links(self):
        links = []
        csv_file_like_object = io.StringIO(self.contents)

        reader = csv.DictReader(csv_file_like_object)
        for row in reader:
            links.append(row["url"])

        return links

    def get_entries(self):
        entries = []
        csv_file_like_object = io.StringIO(self.contents)

        reader = csv.DictReader(csv_file_like_object)
        try:
            for row in reader:
                entries.append(row)
        except csv.Error as e:
            sys.exit("file {}, line {}: {}".format(filename, reader.line_num, e))

        return entries


class ReadingListFile(object):
    def __init__(self, filename=None):
        self.filename = filename

        self.entries = []
        self.read_file()

    def get_entries(self):
        data = None
        with open(self.filename, newline="") as f:
            data = f.read()

        if data:
            r = ReadingList(data)
            return r.get_entries()
