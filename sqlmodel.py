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



class SqlConnection(object):
    """
    Simple wrapper for connection
    """
    def __init__(self, database_file="test.db", parser=None):
        self.conn = None
        self.cursor = None
        self.database_file = database_file

        self.parser = parser

        if not self.create_database():
            print("Could not connect to database")
            return

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

    def commit(self):
        if self.transaction:
            try:
                self.transaction.commit()
            except Exception as e:
                self.transaction.rollback()

            self.transaction = self.conn.begin()

    def close(self):
        if self.transaction:
            try:
                self.transaction.commit()
            except Exception as e:
                self.transaction.rollback()

        self.conn.close()
        self.engine.dispose()

    def get_database_file(self):
        return self.database_file


class GenericTable(object):
    def __init__(self, sqlconnection):
        self.conn = sqlconnection

        self.table_name = None
        self.table = None

    def create(self):
        """
        Expected to set self.table
        """
        raise NotImplementedError("GenericTable: create function has not been implemeneted")

    def count(self):
        from sqlalchemy.sql import text
        st = select(func.count()).select_from(text(self.table_name))
        return self.get_connection().execute(st).scalar()

    def select(self):
        query = select(self.table)
        result = self.get_connection().execute(query)
        return result.fetchall()

    def truncate(self):
        self.conn.execute("TRUNCATE TABLE {}".format(table_name))

    def get_connection(self):
        return self.conn.conn

    def commit(self):
        self.conn.commit()


class EntriesTable(GenericTable):
    def __init__(self, conn, preserve_ids = False):
        super().__init__(conn)
        self.table_name = "entries"
        self.preserve_ids = preserve_ids

    def create(self):
        metadata = MetaData()

        self.table = Table(
            self.table_name,
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

        engine = self.conn.engine
        with engine.connect() as connection:
            if not engine.dialect.has_table(connection, "entries"):
                print("Does not have entries table, creating one")
                metadata.create_all(self.engine)

    def add_entry(self, entry):
        if self.preserve_ids:
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
            self.get_connection().execute(self.table.insert(), [data])

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
            self.get_connection().execute(self.table.insert(), [data])

        except Exception as e:
            print(e)
            return False
        return True

    def is_entry(self, entry):
        query = select(self.table).where(self.table.c.link == entry["link"])

        result = self.get_connection().execute(query)
        row = result.fetchone()

        if row:
            return True
        else:
            return False

    def select(self, conditions=None):
        if conditions:
            query = select(self.table).where(conditions).order_by(self.table.c.date_published.desc())

            result = self.get_connection().execute(query)
            return result.fetchall()
        else:
            query = select(self.table).order_by(self.table.c.date_published.desc())
            result = self.get_connection().execute(query)
            return result.fetchall()

    def remove(self, days):
        now = datetime.now(timezone.utc)
        limit = now - timedelta(days = days)
        query = delete(self.table).where(self.table.c.date_published < limit)
        result = self.get_connection().execute(query)
        return result


class SourcesTable(GenericTable):
    def __init__(self, conn):
        super().__init__(conn)
        self.table_name = "sources"

    def create(self):
        metadata = MetaData()

        self.table = Table(
            self.table_name,
            metadata,
            Column("id", Integer, primary_key=True),
            Column("url", String, unique=True),
            Column("title", String),
        )

        engine = self.get_connection().engine
        with engine.connect() as connection:
            if not engine.dialect.has_table(connection, "sources"):
                print("Does not have sources table, creating one")
                metadata.create_all(self.engine)

    def add_source(self, source):
        """
        Source is a map of props
        """
        try:
            self.get_connection().execute(self.table.insert(), [source])

        except Exception as e:
            print(e)
            return False
        return True

    def is_source(self, source):
        query = select(self.table).where(self.table.c.url == source["url"])

        result = self.get_connection().execute(query)
        row = result.fetchone()

        if row:
            return True
        else:
            return False

    def select(self):
        query = select(self.table)
        result = self.get_connection().execute(query)
        return result.fetchall()

    def remove(self, source_url):
        query = delete(self.table).where(self.table.c.url == source_url)
        result = self.get_connection().execute(query)
        return result


class SqlModel(object):
    def __init__(self, database_file="test.db", parser=None):
        self.conn = SqlConnection(database_file=database_file)

        self.entries_table = EntriesTable(self.conn)
        self.entries_table.create()

        self.sources_table = SourcesTable(self.conn)
        self.sources_table.create()

    def commit(self):
        self.conn.commit()

    def close(self):
        self.conn.close()
