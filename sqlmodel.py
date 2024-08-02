"""
Library package.
"""

from sqlalchemy import (
    create_engine,
    Table,
    MetaData,
    select,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
)


class SqlModel(object):
    def __init__(self, db_file="test.db", parser=None):
        self.conn = None
        self.cursor = None

        if db_file:
            self.db_file = db_file
        else:
            self.db_file = "test.db"

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
            # self.engine = create_engine('sqlite:///'+file_name, echo=True)
            self.engine = create_engine("sqlite:///" + file_name)
            return True
        except Exception as e:
            print(
                "Could not create sqlite3 database file:{}. Exception:{}".format(
                    file_name, str(e)
                )
            )
            return False

    def define_tables(self):
        metadata = MetaData()

        self.entries = Table(
            "entries",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("link", String, unique=True),
            Column("title", String),
            Column("description", String),
            Column("thumbnail", String, nullable=True),
            Column("language", String, nullable=True),
            Column("age", Integer, default=0),
            Column(
                "date_created", DateTime, nullable=True
            ),  # TODO convert to timestamp
            Column("date_published", DateTime, nullable=True),
            Column("date_update_last", DateTime, nullable=True),
            Column("date_dead_since", DateTime, nullable=True),
            Column("date_last_modified", DateTime, nullable=True),
            Column("status_code", Integer, default=0),
            Column("page_rating", Integer, default=0),
            Column("page_rating_votes", Integer, default=0),
            Column("page_rating_contents", Integer, default=0),
            Column("dead", Boolean, default=False),
            Column("bookmarked", Boolean, default=False),
            Column("permanent", Boolean, default=False),
            Column("source", String, nullable=True),
            # advanced / foreign
            Column("source_obj__id", Integer, nullable=True),
            Column("tags", String, nullable=True),
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
            self.conn.execute(self.entries.insert(), [data])

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
            self.conn.execute(self.entries.insert(), [data])

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

    def select_conditions(self, conditions):
        query = select(self.entries).where(conditions)

        result = self.conn.execute(query)
        return result.fetchall()

    def get_database_file(self):
        return self.db_file

    def close(self):
        try:
            self.transaction.commit()
        except Exception as e:
            self.transaction.rollback()

        self.conn.close()
        self.engine.dispose()
