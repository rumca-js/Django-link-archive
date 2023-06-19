import csv
import sys

"""
https://www.tdpain.net/blog/a-year-of-reading
"""


class ReadingList(object):
    def __init__(self, filename=None):
        self.entries = []
        self.filename = filename
        self.read_file()

    def read_file(self):
        with open(self.filename, newline='') as f:
            reader = csv.DictReader(f)
            try:
                for row in reader:
                    self.handle_row(row)
            except csv.Error as e:
                sys.exit('file {}, line {}: {}'.format(filename, reader.line_num, e))

    def handle_row(self, row):
        self.entries.append(row)
