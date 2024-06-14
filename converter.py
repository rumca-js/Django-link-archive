"""
This project can produce SQLite database from JSON files.

SQLite can easily be imported and used by other projects.
"""

import os
import sqlite3
import json
import argparse


class EntryTable(object):
    """
    Low level database implementation. Maybe use sqlalchemy?
    """
    def __init__(self):
        self.fields = [
                {"name" : 'id',                    "properties" : "INTEGER AUTO_INCREMENT PRIMARY KEY"},
                {"name" : 'link',                  "properties" : "TEXT NOT NULL UNIQUE"},
                {"name" : 'title',                 "properties" : "TEXT NOT NULL"},
                {"name" : 'description',           "properties" : "TEXT NOT NULL"},
                {"name" : 'thumbnail',             "properties" : "TEXT NULL"},
                {"name" : 'language',              "properties" : "TEXT NULL"},
                {"name" : 'age',                   "properties" : "INTEGER"},
                {"name" : 'date_created',          "properties" : "TEXT NULL"},
                {"name" : 'date_published',        "properties" : "TEXT NULL"},
                {"name" : 'date_update_last',      "properties" : "TEXT NULL"},
                {"name" : 'date_dead_since',       "properties" : "TEXT NULL"},
                {"name" : 'date_last_modified',    "properties" : "TEXT NULL"},
                {"name" : 'status_code',           "properties" : "INTEGER NULL"},
                {"name" : 'tags',                  "properties" : "TEXT NULL"},
                {"name" : 'page_rating',           "properties" : "INTEGER"},
                {"name" : 'page_rating_votes',     "properties" : "INTEGER"},
                {"name" : 'page_rating_contents',  "properties" : "INTEGER"},
                ]

    def get_query_create_table(self):
        query_start = """
        CREATE TABLE IF NOT EXISTS entries (
        """
        query_stop = """
            )
        """

        fields_len = len(self.fields)

        query_body = ""
        for key, field in enumerate(self.fields):
            query_body += field["name"] + " " + field["properties"]

            if key != fields_len -1:
                query_body += ","

        return query_start + query_body + query_stop

    def get_query_insert(self, entry_dict, auto_increment = False):
        query_start = """
        INSERT INTO entries (
        """
        query_stop = """
        )
        """

        values_start = """ VALUES (
        """
        values_stop = """
        )
        """

        fields_len = len(self.fields)

        query_body = ""
        for key, field in enumerate(self.fields):
            if auto_increment == True and field["name"] == "id":
                continue

            query_body += field["name"]

            if key != fields_len -1:
                query_body += ","

        values_body = ""
        for key, field in enumerate(self.fields):
            if auto_increment == True and field["name"] == "id":
                continue

            value = self.get_entry_value(field, entry_dict)
            values_body += "'" + str(value) + "'"

            if key != fields_len -1:
                values_body += ","

        return query_start + query_body + query_stop + values_start + values_body + values_stop

    def get_entry_value(self, field, entry_dict):
        field_name = field["name"]
        field_props = field["properties"]

        if field_name not in entry_dict or entry_dict[field_name] is None:
            if field_props.find("TEXT") >= 0:
                return ""
            elif field_props.find("INTEGER") >= 0:
                return 0
        else:
            entry_value = entry_dict[field_name]
            if type(entry_value) == list:
                entry_value = ", ".join(entry_value)

            if field_props.find("TEXT") >= 0:
                if entry_value.find("'") >= 0:
                    entry_value = entry_value.replace("'", "")

            return entry_value

    def get_query_is_entry(self, entry):
        query = """
        SELECT * FROM entries WHERE link = '{}'
        """.format(entry["link"])

        return query


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
        self.cursor = None

        if output_file:
            self.output_file = output_file
        else:
            self.output_file = "test.db"

        self.parser = parser

        self.entry_table = EntryTable()

        self.create_database()
        self.create_entry_table()

    def create_database(self):
        file_name = self.get_database_file()

        try:
            self.conn = sqlite3.connect(file_name)
            self.cursor = self.conn.cursor()
        except Exception as E:
            print("Could not create sqlite3 database file:{}. Exception:{}".format(file_name, str(E)))

    def create_entry_table(self):
        query = self.entry_table.get_query_create_table()
        #print(query)
        self.cursor.execute(query)

    def add_entry(self, entry):
        if self.parser and self.parser.preserve_id:
            self.add_entry_as_is(entry)
        else:
            self.add_entry_auto_increment(entry)

    def add_entry_auto_increment(self, entry):
        query = self.entry_table.get_query_insert(entry, auto_increment=True)
        #print(query)
        self.cursor.execute(query)

    def add_entry_as_is(self, entry):
        query = self.entry_table.get_query_insert(entry, auto_increment=False)
        #print(query)
        self.cursor.execute(query)

    def is_entry(self, entry):
        query = self.entry_table.get_query_is_entry(entry)
        #print(query)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()

        return len(rows) > 0

    def get_database_file(self):
        return self.output_file

    def close(self):
        if self.conn:
            self.conn.commit()
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

                if not self.conn.is_entry(entry):
                    print(" -> [{}/{}] Link:{} Added".format(row, total_rows, entry["link"]))
                    self.conn.add_entry(entry)
                else:
                    print(" -> [{}/{}] Link:{} Skipped".format(row, total_rows, entry["link"]))

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
