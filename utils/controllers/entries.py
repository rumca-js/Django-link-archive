from webtools import Url

from utils.sqlmodel import (
    SqlModel,
    EntriesTable,
    EntriesTableController,
    SourcesTable,
    SourcesTableController,
    SourceOperationalData,
    SourceOperationalDataController,
)


class EntryDataBuilder(object):
    def __init__(
        self,
        conn,
        link=None,
        link_data=None,
        manual_entry=False,
        allow_recursion=True,
        ignore_errors=False):

        self.conn = conn
        self.link = link
        self.link_data = link_data

    def get_session(self):
        return self.conn.get_session()

    def build(self,
        link=None,
        link_data=None,
        manual_entry=False,
        allow_recursion=True,
        ignore_errors=False):

        if link:
            self.link = link
        if link_data:
            self.link_data = link_data

        if self.link_data:
            self.build_from_props()
        elif self.link:
            self.build_from_link()

    def build_from_link(self):
        rss_url = self.link

        if rss_url.endswith("/"):
            rss_url = rss_url[:-1]

        h = Url(rss_url)
        if not h.is_valid():
            return

        self.link_data = h.get_properties()

        return self.build_from_props()

    def build_from_props(self):
        Session = self.get_session()
        with Session() as session:
            table = EntriesTable(**self.link_data)

            session.add(table)
            session.commit()
