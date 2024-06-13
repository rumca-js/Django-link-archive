"""
This project can produce SQLite database from JSON files.

SQLite can easily be imported and used by other projects.
"""

import os
import sqlite3
import json
import argparse


class DirReader(object):

    def __init__(self, source_files_directory, accepted_extensions = None):
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


class DataBase(object):
    def __init__(self, output_file = "test.db", parser = None):
        self.conn = None
        if output_file:
            self.output_file = output_file
        else:
            self.output_file = "test.db"

        self.parser = parser

        self.create_database()
        self.create_entry_table()

    def create_database(self):
        file_name = self.get_database_file()

        try:
            self.conn = sqlite3.connect(file_name)
        except Exception as E:
            print("Could not create sqlite3 database file:{}. Exception:{}".format(file_name, str(E)))

    def create_entry_table(self):
        query = """
        CREATE TABLE IF NOT EXISTS entries (
            id INTEGER AUTO_INCREMENT PRIMARY KEY,
            link TEXT NOT NULL UNIQUE,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            date_published TEXT NULL,
            page_rating INTEGER,
            page_rating_votes INTEGER,
            language TEXT NULL,
            status_code INTEGER NULL
            )
        """

        c = self.conn.cursor()
        c.execute(query)
        self.conn.commit()

    def add_entry(self, entry):
        self.clean_up_entry(entry)

        if self.parser and self.parser.preserve_id:
            self.add_entry_as_is(entry)
        else:
            self.add_entry_auto_increment(entry)

    def clean_up_entry(self, entry):
        if "title" not in entry:
            entry["title"] = ""
        if "description" not in entry:
            entry["description"] = ""
        if "date_published" not in entry:
            entry["date_published"] = ""
        if "page_rating" not in entry:
            entry["page_rating"] = 0
        if "page_rating_votes" not in entry:
            entry["page_rating_votes"] = 0
        if "language" not in entry:
            entry["language"] = ""
        if "status_code" not in entry:
            entry["status_code"] = 0

    def add_entry_auto_increment(self, entry):

        # TODO maybe we should encapsulate, unescape, or something. This is ugly
        title = entry["title"].replace("'", "")
        description = entry["description"].replace("'", "")

        query = """
        INSERT INTO entries (
            link,
            title,
            description,
            date_published,
            page_rating,
            page_rating_votes,
            language,
            status_code)
            VALUES
            ('{}','{}','{}','{}','{}','{}','{}','{}')
        """.format(entry["link"],
                title,
                description,
                entry["date_published"],
                entry["page_rating"],
                entry["page_rating_votes"],
                entry["language"],
                entry["status_code"],
                )

        c = self.conn.cursor()
        c.execute(query)
        self.conn.commit()

    def add_entry_as_is(self, entry):
        print("Adding entry:{}".format(entry))

        query = """
        INSERT INTO entries (
            link)
            VALUES
            ('{}')
        """.format(entry["link"])

        c = self.conn.cursor()
        c.execute(query)
        self.conn.commit()

    def is_entry(self, entry):
        query = """
        SELECT * FROM entries WHERE link = '{}'
        """.format(entry["link"])

        c = self.conn.cursor()
        c.execute(query)
        rows = c.fetchall()

        return len(rows) > 0

    def get_database_file(self):
        return self.output_file

    def close(self):
        if self.conn:
            self.conn.close()


class Converter(object):
    """
    Performs actual conversion between file and database
    """
    def __init__(self, db_conn, parser):
        self.conn = db_conn
        self.parser = parser
        self.file_reader = DirReader(source_files_directory = parser.dir)
        self.files = self.file_reader.get_files()

    def convert(self):
        for afile in self.files:
            self.convert_file(afile)

    def convert_file(self, file_name):
        data = self.read_file(file_name)
        if not data:
            return

        for key, entry in enumerate(data):
            if "link" in entry:
                if self.parser and self.parser.preserve_id:
                    if "id" not in entry:
                        print("Entry {} is missing ID".format(entry["link"]))
                        continue
                else:
                    entry["id"] = key

                if not self.conn.is_entry(entry):
                    print("Adding entry:{}".format(entry.link))
                    self.conn.add_entry(entry)
                else:
                    print("NOT adding entry:{}".format(entry.link))

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
        except Exception as E:
            print("Could not read file: {}".format(afile))


class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data converter program")
        self.parser.add_argument("--dir", help="Directory to be scanned")
        self.parser.add_argument("--output-file", help="Output file")
        self.parser.add_argument("--preserve-id", action="store_true", help="Preserves ID of objects")
        self.parser.add_argument("--language", help="Accept language") # TODO implement
        self.parser.add_argument("--vote-min", help="Minimum amount of entry vote") # TODO implement

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


def main():
    print("Starting processing")
    parser = Parser()
    parser.parse()

    db = DataBase(output_file = parser.output_file)

    c = Converter(db, parser)
    c.convert()

    db.close()
    print("Processing DONE")

main()
