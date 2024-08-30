"""
Library package.
"""

from typing import Optional
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
    update,
)
from sqlalchemy.orm import sessionmaker
import sqlalchemy
from datetime import timedelta, datetime, timezone


from sqlalchemy.orm import Session
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column


def create_this_engine():
    file_name = "test.db"
    return create_engine("sqlite:///" + file_name)


class SqlConnection(object):
    """
    Simple wrapper for connection
    """
    def __init__(self, database_file="test.db", parser=None):
        self.cursor = None
        self.database_file = database_file

        self.parser = parser

        if not self.create_database():
            print("Could not connect to database")
            return

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

    def close(self):
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
        if self.table_name:
            truncate_query = sqlalchemy.text("DELETE FROM {}".format(self.table_name))
            self.get_connection().execute(truncate_query)
            self.commit()

    def get_connection(self):
        return self.conn.conn

    def commit(self):
        self.conn.commit()


class Base(DeclarativeBase):
    pass


class EntriesTable(Base):
    __tablename__ = "entries"

    id: Mapped[int] = mapped_column(primary_key=True)
    link: Mapped[str] = mapped_column(String(30), unique=True)
    title: Mapped[str]
    description: Mapped[Optional[str]]
    thumbnail: Mapped[Optional[str]]
    language: Mapped[Optional[str]]
    age: Mapped[int] = mapped_column(default=0)
    date_created = mapped_column(DateTime, nullable=True)
    date_published= mapped_column(DateTime, nullable=True)
    date_update_last= mapped_column(DateTime, nullable=True)
    date_dead_since= mapped_column(DateTime, nullable=True)
    date_last_modified= mapped_column(DateTime, nullable=True)
    status_code: Mapped[int] = mapped_column(default=0)
    page_rating: Mapped[int] = mapped_column(default=0)
    page_rating_votes: Mapped[int] = mapped_column(default=0)
    page_rating_contents: Mapped[int] = mapped_column(default=0)
    dead: Mapped[bool] = mapped_column(default=False)
    bookmarked: Mapped[bool] = mapped_column(default=False)
    permanent: Mapped[bool] = mapped_column(default=False)
    source: Mapped[Optional[str]]
    artist: Mapped[Optional[str]]
    album: Mapped[Optional[str]]
    # advanced / foreign
    source_obj__id: Mapped[Optional[int]]
    tags: Mapped[Optional[str]]


class EntriesTableController(object):
    def __init__(self, db, session = None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.session_factory()
        else:
            return self.session

    def remove(self, days):
        now = datetime.now(timezone.utc)
        limit = now - timedelta(days = days)

        session = self.get_session()

        entries = session.query

        query = delete(EntriesTable).where(EntriesTable.date_published < limit)
        session.execute(query)
        session.commit()

    def add_entry(self, entry):
        if "author" in entry:
            entry["artist"] = entry["author"]
            del entry["author"]

        if "tags" in entry:
            try:
                if entry["tags"]:
                    entry["tags"] = ", ".join(entry["tags"])
            except Exception as E:
                data["tags"] = None

        if "feed_entry" in entry:
            del entry["feed_entry"]

        if "source_title" in entry:
            del entry["source_title"]

        entry_obj = EntriesTable(**entry)

        session = self.get_session()
        session.add(entry_obj)
        session.commit()


class SourcesTable(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    url : Mapped[str] = mapped_column(unique=True)
    title: Mapped[str]


class SourcesTableController(object):

    def __init__(self, db, session = None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.session_factory()
        else:
            return self.session

    def get_all(self):
        session = self.get_session()
        sources = session.query(SourcesTable).all()
        return sources


class SourceOperationalData(Base):
    __tablename__ = "sourceoperationaldata"

    id: Mapped[int] = mapped_column(primary_key=True)
    date_fetched = mapped_column(DateTime, nullable=True)
    source_obj_id: Mapped[int]


class SourceOperationalDataController(object):

    def __init__(self, db, session = None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.session_factory()
        else:
            return self.session

    def is_fetch_possible(self, source, date_now, limit_seconds=60 * 10):
        session = self.get_session()

        rows = session.query(SourceOperationalData).filter(SourceOperationalData.source_obj_id == source.id).all()

        if len(rows) == 0:
            return True

        row = rows[0]

        source_datetime = row.date_fetched

        diff = date_now - source_datetime

        if diff.total_seconds() > limit_seconds:
            return True
        return False

    def set_fetched(self, source, date_now):
        session = self.get_session()

        op_data = session.query(SourceOperationalData).filter(SourceOperationalData.source_obj_id == source.id).all()
        if len(op_data) == 0:
            obj = SourceOperationalData(date_fetched = date_now, source_obj_id = source.id)
            session.add(obj)
            session.commit()
        else:
            op_data = op_data[0]
            op_data.date_fetched = date_now
            session.commit()


class SqlModel(object):
    def __init__(self, database_file="test.db", parser=None, engine=None):
        self.db_file = database_file

        if not engine:
            self.engine = create_engine("sqlite:///" + self.db_file)
        else:
            self.engine = engine

    def session_factory(self):
        _SessionFactory = sessionmaker(bind=self.engine)

        Base.metadata.create_all(self.engine)
        return _SessionFactory()
