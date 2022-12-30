import csv
import sys

"""
def __init__(self, data = None):
    self.entries = []
    if data:
        self.process_string(data)

def process_string(self, data, delimiter = "\n"):
    entries = data.split(delimiter)

    # first line is a comment
    index = 0

    for entry_row in entries:
        index += 1

        if index == 1:
            continue

        entry_row = entry_row.replace("\r", "")
        if entry_row.strip() != "":
            print(entry_row)
            entry = ReadingListLine(entry_row)
            self.entries.append(entry)
"""

class ReadingListLine(object):
    def __init__(self, line, line_delimiter = ','):
        self.delimiter = line_delimiter
        self.line = line

        link_info = line.split(self.delimiter)

        self.url = link_info[0]
        self.title = link_info[1]
        self.description = link_info[2]
        self.image = link_info[3]
        self.date = link_info[4]
        self.hnurl = link_info[5]

        print(self.date)

        self.date = self.convert_date(self.date)

    def convert_date(self, timestamp):
       from dateutil import parser
       date = parser.parse(timestamp)
       date = date.isoformat()
       return date

class ReadingList(object):
    def __init__(self, filename = None):
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
