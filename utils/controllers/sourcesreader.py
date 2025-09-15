from datetime import timedelta, datetime, timezone
from utils.dateutils import DateUtils

from rsshistory.webtools import RemoteServer
from rsshistory.configuration import Configuration

from utils.sqlmodel import SourcesTable
from utils.controllers import (
    EntriesTableController,
    SourcesTableController,
    SourceOperationalDataController,
    ConfigurationEntryController,
    EntryWrapper,
)


class SourceReader(object):
    def __init__(self, db, session=None):
        self.conn = db
        self.session = session
        self.day_limit = 10

        c = Configuration.get_object()
        self.server_location = c.crawler_location

    def get_session(self):
        if not self.session:
            return self.conn.get_session()
        else:
            return self.session

    def read(self):
        print("Removing entries")
        entries = EntriesTableController(self.conn)
        entries.remove(self.day_limit)

        print("Fetching entries")
        self.fetch(self.day_limit, self.server_location)
        # asyncio.run(fetch(self.db, self.parser, self.day_limit))
        date_now = DateUtils.get_datetime_now_utc()
        print("Current time:{}".format(date_now))

    def fetch(self, day_limit, server_location="http://127.0.0.1:3000"):
        """
        fetch time is used to not spam servers every time you refresh anything
        """
        sources = SourcesTableController(self.conn).filter(
            conditions=[SourcesTable.enabled == True]
        )

        for source in sources:
            date_now = DateUtils.get_datetime_now_utc()
            date_now = date_now.replace(tzinfo=None)

            force = False

            if not force:
                operational_data = SourceOperationalDataController(self.conn)
                if not operational_data.is_fetch_possible(source, date_now, 60 * 10):
                    continue

            date_now = DateUtils.get_datetime_now_utc()
            date_now = date_now.replace(tzinfo=None)
            op_con = SourceOperationalDataController(self.conn)
            op_con.set_fetched(source, date_now)

            print("Reading {}".format(source.url))
            source_entries = self.read_source(source, server_location)

            for entry in source_entries:
                now = datetime.now(timezone.utc)
                limit = now - timedelta(days=day_limit)

                wrapper = EntryWrapper(self.conn, link=entry["link"])
                entry_object = wrapper.get()

                if entry_object:
                    continue

                date_published = entry["date_published"]
                date_published = DateUtils.parse_datetime(date_published)
                entry["date_published"] = date_published

                if date_published > limit:
                    ec = EntriesTableController(self.conn)
                    ec.add(entry)

            controller = EntriesTableController(self.conn)
            count = controller.count()
            print(f"Number of entries:{count}")

    def read_source(self, source, server_location="http://127.0.0.1:3000"):
        result = []

        source_url = source.url
        source_title = source.title
        source_id = source.id

        remote = RemoteServer(server_location)
        all_properties = remote.get_getj(source_url)

        entries = remote.read_properties_section("Entries", all_properties)

        if not entries:
            print("Cannot obtain entries for:{}".format(source_url))
            return result

        for item in entries:
            item["source_url"] = source_url
            item["source"] = source_id
            result.append(item)

        return result
