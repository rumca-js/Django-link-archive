"""
Library package.
"""

from sqlalchemy import (
    create_engine,
    Table,
    MetaData,
    select,
    func,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    delete,
)
from datetime import timedelta, datetime, timezone


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
        self.define_entries()
        self.define_sources()

    def define_entries(self):
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
                print("Does not have entries table, creating one")
                metadata.create_all(self.engine)

    def define_sources(self):
        metadata = MetaData()

        self.sources = Table(
            "sources",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("url", String, unique=True),
            Column("title", String),
        )

        with self.engine.connect() as connection:
            if not self.engine.dialect.has_table(connection, "sources"):
                print("Does not have sources table, creating one")
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
                if entry[key]:
                    data[key] = ", ".join(entry[key])
                else:
                    data[key] = None

            elif key.startswith("date"):
                if type(entry[key]) == str:
                    date = parser.parse(entry[key])
                    data[key] = date
                else:
                    data[key] = entry[key]
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
                if entry[key]:
                    data[key] = ", ".join(entry[key])
                else:
                    data[key] = None
            elif key.startswith("date"):
                if type(entry[key]) == str:
                    date = parser.parse(entry[key])
                    data[key] = date
                else:
                    data[key] = entry[key]
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

    def add_source(self, source):
        """
        Source is a map of props
        """
        try:
            self.conn.execute(self.sources.insert(), [source])

        except Exception as e:
            print(e)
            return False
        return True

    def is_source(self, source):
        query = select(self.sources).where(self.sources.c.url == source["url"])

        result = self.conn.execute(query)
        row = result.fetchone()

        if row:
            return True
        else:
            return False

    def count(self, table):
        st = select(func.count()).select_from(table)
        return self.conn.execute(st).scalar()

    def select_entries(self, conditions=None):
        if conditions:
            query = select(self.entries).where(conditions).order_by(self.entries.c.date_published.desc())

            result = self.conn.execute(query)
            return result.fetchall()
        else:
            query = select(self.entries).order_by(self.entries.c.date_published.desc())
            result = self.conn.execute(query)
            return result.fetchall()

    def select_sources(self):
        query = select(self.sources)
        result = self.conn.execute(query)
        return result.fetchall()

    def get_database_file(self):
        return self.db_file

    def commit(self):
        if self.transaction:
            try:
                self.transaction.commit()
            except Exception as e:
                self.transaction.rollback()

            self.transaction = self.conn.begin()

    def truncate(self, table_name):
        self.conn.execute("TRUNCATE TABLE {}".format(table_name))

    def close(self):
        if self.transaction:
            try:
                self.transaction.commit()
            except Exception as e:
                self.transaction.rollback()

        self.conn.close()
        self.engine.dispose()

    def remove_older_than_days(self, days):
        now = datetime.now(timezone.utc)
        limit = now - timedelta(days = days)
        query = delete(self.entries).where(self.entries.c.date_published < limit)
        result = self.conn.execute(query)
        return result

    def remove_source(self, source_url):
        query = delete(self.sources).where(self.sources.c.url == source_url)
        result = self.conn.execute(query)
        return result
