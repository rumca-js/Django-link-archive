"""
This project can produce SQLite database from JSON files.

SQLite can easily be imported and used by other projects.
"""

import os
import sqlite3
import json
import argparse
import time

from sqlalchemy import create_engine, Table, MetaData, select, Column, Integer, String, Boolean, DateTime
from dateutil import parser



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

        if not self.create_database():
            print("Could not connect to database")
            return

        self.define_tables()
        self.conn = self.engine.connect()
        self.transaction = self.conn.begin()

    def create_database(self):
        file_name = self.get_database_file()

        try:
            #self.engine = create_engine('sqlite:///'+file_name, echo=True)
            self.engine = create_engine('sqlite:///'+file_name)
            return True
        except Exception as e:
            print("Could not create sqlite3 database file:{}. Exception:{}".format(file_name, str(e)))
            return False

    def define_tables(self):
        metadata = MetaData()

        self.entries = Table(
           'entries', metadata,
           Column('id', Integer, primary_key=True),
           Column('link',                  String, unique=True),
           Column('title',                 String),
           Column('description',           String),
           Column('thumbnail',             String, nullable=True),
           Column('language',              String, nullable=True),
           Column('age',                   Integer, default=0),
           Column('date_created',          DateTime, nullable=True), # TODO convert to timestamp
           Column('date_published',        DateTime, nullable=True),
           Column('date_update_last',      DateTime, nullable=True),
           Column('date_dead_since',       DateTime, nullable=True),
           Column('date_last_modified',    DateTime, nullable=True),
           Column('status_code',           Integer, default=0),
           Column('page_rating',           Integer, default=0),
           Column('page_rating_votes',     Integer, default=0),
           Column('page_rating_contents',  Integer, default=0),
           Column('dead',                  Boolean, default=False),
           Column('bookmarked',            Boolean, default=False),
           Column('permanent',             Boolean, default=False),
           Column('source',                String, nullable=True),

           # advanced / foreign
           Column('source_obj__id',        Integer, nullable=True),
           Column('tags',                  String, nullable=True),
        )

        with self.engine.connect() as connection:
            if not self.engine.dialect.has_table(connection, "entries"):
                print("Does not have table, creating one")
                metadata.create_all(self.engine)

    def add_entry(self, entry):
        if self.parser and self.parser.preserve_id:
            return self.add_entry_as_is(entry)
        else:
            return self.add_entry_auto_increment(entry)

    def add_entry_auto_increment(self, entry):
        data = {}
        for key in entry:
            if key == "id":
                continue
            elif key == "tags":
                data[key] = ", ".join(entry[key])
            elif key.startswith("date"):
                date = parser.parse(entry[key])
                data[key] = date
            else:
                data[key] = entry[key]

        try:
            self.conn.execute(
                self.entries.insert(),
                [
                    data
                ]
            )

        except Exception as e:
            print(e)
            return False
        return True

    def add_entry_as_is(self, entry):
        data = {}
        for key in entry:
            if key == "tags":
                data[key] = ", ".join(entry[key])
            elif key.startswith("date"):
                date = parser.parse(entry[key])
                data[key] = date
            else:
                data[key] = entry[key]

        try:
            self.conn.execute(
                self.entries.insert(),
                [
                    data
                ]
            )

        except Exception as e:
            print(e)
            return False
        return True

    def is_entry(self, entry):
        query = select(self.entries).where(self.entries.c.link == entry["link"])

        result = self.conn.execute(query)
        row = result.fetchone()

        if row:
            return True
        else:
            return False

    def get_database_file(self):
        return self.output_file

    def close(self):
        try:
            self.transaction.commit()
        except Exception as e:
            self.transaction.rollback()

        self.conn.close()
        self.engine.dispose()


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
                    if self.conn.add_entry(entry):
                        if self.parser.args.verbose:
                            print(" -> [{}/{}] Link:{} Added".format(row, total_rows, entry["link"]))
                    else:
                        print(" -> [{}/{}] Link:{} NOT Added".format(row, total_rows, entry["link"]))
                else:
                    if self.parser.args.verbose:
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
        except Exception as e:
            print("Could not read file: {}".format(afile))


class Parser(object):

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data converter program")
        self.parser.add_argument("--dir", help="Directory to be scanned")
        self.parser.add_argument("--output-file", help="Output file")
        self.parser.add_argument("--preserve-id", action="store_true", help="Preserves ID of objects")
        self.parser.add_argument("--language", help="Accept language") # TODO implement
        self.parser.add_argument("--vote-min", help="Minimum amount of entry vote") # TODO implement
        self.parser.add_argument("--entries", help="Convert entries") # TODO implement
        self.parser.add_argument("--sources", help="Convert sources") # TODO implement
        self.parser.add_argument("--verbose", action="store_true", help="Shows more info")

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
