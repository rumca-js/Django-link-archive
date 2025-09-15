from sqlalchemy import desc, asc
from utils.sqlmodel import (
    SourcesTable,
    SourceOperationalData,
)


class SourcesTableController(object):
    def __init__(self, db, session=None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.get_session()
        else:
            return self.session

    def get(self, id):
        Session = self.get_session()

        with Session() as session:
            query = session.query(SourcesTable)

            query = query.filter(SourcesTable.id == id)

            return query.first()

    def all(self):
        sources = []

        Session = self.get_session()
        with Session() as session:
            sources = session.query(SourcesTable).all()

        return sources

    def filter(self, conditions=None, ascending=True, page=1, rows_per_page=200):
        Session = self.conn.get_session()

        with Session() as session:
            query = session.query(SourcesTable)

            if conditions:
                for condition in conditions:
                    query = query.filter(condition)

            if ascending:
                query = query.order_by(asc(SourcesTable.id))
            else:
                query = query.order_by(desc(SourcesTable.id))

            offset = (page - 1) * rows_per_page
            query = query.offset(offset).limit(rows_per_page)

            return query.all()

    def is_source(self, id=None, url=None):
        is_source = False
        Session = self.get_session()

        with Session() as session:
            if id:
                exists = (
                    session.query(SourcesTable)
                    .filter(SourcesTable.id == int(id))
                    .exists()
                )
                if exists:
                    is_source = True
            if url:
                exists = (
                    session.query(SourcesTable).filter(SourcesTable.url == url).exists()
                )
                if exists:
                    is_source = True

        return is_source

    def add(self, source):
        valid_columns = {column.name for column in SourcesTable.__table__.columns}

        source = {key: value for key, value in source.items() if key in valid_columns}

        source_obj = SourcesTable(**source)

        Session = self.get_session()
        with Session() as session:
            session.add(source_obj)
            session.commit()


class SourceDataBuilder(object):
    def __init__(self, conn, link=None, link_data=None, manual_entry=False):
        self.conn = conn
        self.link = link
        self.link_data = link_data

    def get_session(self):
        return self.conn.get_session()

    def build(self, link=None, link_data=None, manual_entry=False):
        if link_data:
            self.link_data = link_data
        if link:
            self.link = link

        if self.link_data:
            return self.build_from_props()
        elif self.link:
            return self.build_from_link()

    def build_from_link(self):
        rss_url = self.link

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        h = Url(rss_url)
        if not h.is_valid():
            return

        self.link_data = h.get_properties()

        return self.build_from_props()

    def is_source(self):
        Session = self.get_session()

        with Session() as session:
            exists = (
                session.query(SourcesTable)
                .filter(SourcesTable.url == self.link_data["url"])
                .exists()
            )
            if exists:
                return True

    def build_from_props(self):
        if self.is_source():
            return

        result = False

        Session = self.get_session()
        with Session() as session:
            table = SourcesTable(**self.link_data)

            session.add(table)
            session.commit()

            result = True

        return result

    def import_source(self, link_data=None):
        """
        importing might be different than building from scratch
        """
        self.build(link_data=link_data)
        print("import test")


def source_to_json(source, user_config=None):
    json_source = {}

    json_source["id"] = source.id
    json_source["url_absolute"] = source.url
    json_source["url"] = source.url
    json_source["enabled"] = source.enabled
    json_source["source_type"] = source.source_type
    json_source["title"] = source.title
    json_source["category_name"] = source.category_name
    json_source["subcategory_name"] = source.subcategory_name
    json_source["export_to_cms"] = source.export_to_cms
    json_source["remove_after_days"] = source.remove_after_days
    json_source["language"] = source.language
    json_source["age"] = source.age
    json_source["favicon"] = source.favicon
    json_source["fetch_period"] = source.fetch_period
    json_source["auto_tag"] = source.auto_tag
    json_source["errors"] = 0

    return json_source


class SourceOperationalDataController(object):
    def __init__(self, db, session=None):
        self.conn = db
        self.session = session

    def get_session(self):
        if not self.session:
            return self.conn.get_session()
        else:
            return self.session

    def is_fetch_possible(self, source, date_now, limit_seconds=60 * 10):
        Session = self.get_session()
        with Session() as session:
            rows = (
                session.query(SourceOperationalData)
                .filter(SourceOperationalData.source == source.id)
                .all()
            )

            if len(rows) == 0:
                return True

            row = rows[0]

            source_datetime = row.date_fetched

            diff = date_now - source_datetime

            if diff.total_seconds() > limit_seconds:
                return True
            return False

    def set_fetched(self, source, date_now):
        Session = self.get_session()
        with Session() as session:
            op_data = (
                session.query(SourceOperationalData)
                .filter(SourceOperationalData.source == source.id)
                .all()
            )
            if len(op_data) == 0:
                obj = SourceOperationalData(date_fetched=date_now, source=source.id)
                session.add(obj)
                session.commit()
            else:
                op_data = op_data[0]
                op_data.date_fetched = date_now
                session.commit()

    def get(self, id):
        Session = self.get_session()

        with Session() as session:
            query = session.query(SourcesTable)

            query = query.filter(SourcesTable.id == id)

            return query.first()
