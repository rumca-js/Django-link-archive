"""
@brief Converts JSON files to SQLite DB

SQLite can easily be imported and used by other projects.
"""

import os
import sqlite3
import json
import argparse
import time

from sqlmodel import SqlModel
from dateutil import parser


class DirReader(object):
    def __init__(self, source_files_directory, accepted_extensions=None):
        self.dir = source_files_directory
        if accepted_extensions is None:
            self.accepted_extensions = [".json"]

    def get_files(self):
        file_list = []
        for root, dirs, files in os.walk(self.dir):
            for file in files:
                file_split = os.path.splitext(file)
                if file_split[1] in self.accepted_extensions:
                    file_list.append(os.path.join(root, file))

        file_list = sorted(file_list)
        return file_list


class Converter(object):
    """
    Performs actual conversion between file and database
    """

    def __init__(self, db_conn, parser):
        self.conn = db_conn
        self.parser = parser
        self.file_reader = DirReader(source_files_directory=parser.dir)
        self.files = self.file_reader.get_files()

    def convert(self):
        total_num_files = len(self.files)

        for row, afile in enumerate(self.files):
            print("[{}/{}]: file:{}".format(row, total_num_files, afile))
            self.convert_file(afile)

    def convert_file(self, file_name):
        data = self.read_file(file_name)
        if not data:
            return

        total_rows = len(data)

        for row, entry in enumerate(data):
            if "link" in entry:
                if self.parser and self.parser.preserve_id:
                    if "id" not in entry:
                        print("Entry {} is missing ID".format(entry["link"]))
                        continue
                else:
                    entry["id"] = row

                if self.is_entry_to_be_added(entry):
                    if self.conn.add_entry(entry):
                        if self.parser.args.verbose:
                            print(
                                " -> [{}/{}] Link:{} Added".format(
                                    row, total_rows, entry["link"]
                                )
                            )
                    else:
                        print(
                            " -> [{}/{}] Link:{} NOT Added".format(
                                row, total_rows, entry["link"]
                            )
                        )
                else:
                    if self.parser.args.verbose:
                        print(
                            " -> [{}/{}] Link:{} Skipped".format(
                                row, total_rows, entry["link"]
                            )
                        )

    def is_entry_to_be_added(self, entry):
        # entry already exists
        if self.conn.is_entry(entry):
            return False

        if self.parser.vote_min:
            if int(entry["page_rating_votes"]) < self.parser.vote_min:
                return False

        return True

    def read_file_contents(self, file_name):
        with open(file_name, "r") as f:
            return f.read()

    def read_file(self, file_name):
        text = self.read_file_contents(file_name)

        try:
            j = json.loads(text)

            if "links" in j:
                return j["links"]
            if "sources" in j:
                return j["sources"]

            return j
        except Exception as e:
            print("Could not read file: {}".format(afile))


class Parser(object):
    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data converter program")
        self.parser.add_argument("--dir", help="Directory to be scanned")
        self.parser.add_argument("--output-file", help="Output file")
        self.parser.add_argument(
            "--preserve-id", action="store_true", help="Preserves ID of objects"
        )
        self.parser.add_argument("--vote-min", help="Minimum amount of entry vote")
        self.parser.add_argument("--language", help="Accept language")  # TODO implement
        self.parser.add_argument("--entries", help="Convert entries")  # TODO implement
        self.parser.add_argument("--sources", help="Convert sources")  # TODO implement
        self.parser.add_argument(
            "--verbose", action="store_true", help="Shows more info"
        )

        self.args = self.parser.parse_args()

        if self.args.dir:
            self.dir = self.args.dir
        else:
            self.dir = None

        if self.args.output_file:
            self.output_file = self.args.output_file
        else:
            self.output_file = None

        if self.args.preserve_id:
            self.preserve_id = self.args.preserve_id
        else:
            self.preserve_id = None

        if self.args.vote_min:
            self.vote_min = int(self.args.vote_min)
        else:
            self.vote_min = None


def main():
    print("Starting processing")
    parser = Parser()
    parser.parse()

    db = SqlModel(db_file=parser.output_file)

    try:
        start_time = time.time()

        c = Converter(db, parser)
        c.convert()

        elapsed_time_seconds = time.time() - start_time
        elapsed_minutes = int(elapsed_time_seconds // 60)
        elapsed_seconds = int(elapsed_time_seconds % 60)
        print(f"Time: {elapsed_minutes}:{elapsed_seconds}")

    except Exception as e:
        print("Exception: {}".format(e))
    except KeyboardInterrupt as e:
        print("Exception: {}".format(e))

    db.close()
    print("Processing DONE")


main()
