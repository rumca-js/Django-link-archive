"""
This is example script about how to use this project as a simple RSS reader
"""
import argparse
import sys
import asyncio
from pathlib import Path
import shutil
from sqlalchemy import desc

from utils.sqlmodel import (
    SqlModel,
    EntriesTable,
    EntriesTableController,
    SourcesTable,
    SourcesTableController,
    SourceOperationalData,
    SourceOperationalDataController,
)
from datetime import timedelta, datetime, timezone

from webtools import (
    PageOptions,
    WebConfig,
    WebLogger,
    PrintWebLogger,
    Url,
    RssPage,
    HttpPageHandler,
)
from utils.dateutils import DateUtils
from utils.serializers import HtmlExporter
from utils.alchemysearch import AlchemySearch, AlchemyRowHandler


__version__ = "0.0.4"


def print_entry(row):
    id = 0
    if "id" in row:
        id = row["id"]
    page_rating = 0
    if "page_rating" in row:
        page_rating = row["page_rating"]

    title = ""
    if "title" in row:
        title = row["title"]

    link = ""
    if "link" in row:
        link =row["link"]

    date_published = None
    if "date_published" in row:
        date_published =row["date_published"]

    print("[{}/{}] {}".format(id, page_rating, title))
    print(date_published)
    print("{}".format(link))


def print_source(source):
    print("[{}] Title:{} Enabled:{}".format(source.id, source.title, source.enabled))
    print("Url:{}".format(source.url))


def read_source(db, source):
    result = []

    source_url = source.url
    source_title = source.title
    source_id = source.id

    options = PageOptions()
    options.use_headless_browser = False
    options.use_full_browser = False

    url = Url(url = source_url, page_options = options)
    handler = url.get_handler()
    response = url.get_response()

    if not handler:
        print("Cannot obtain handler for:{}".format(source_url))
        return

    if response:
        entries = handler.get_entries()

        if not entries:
            print("Cannot obtain entries for:{}".format(source_url))
            return result

        for item in entries:
            item["source"] = source_url
            item["source_title"] = source_title
            item["source_obj__id"] = source_id
            result.append(item)

    print("\rRead:{}".format(source_url), end="")

    return result


class OutputWriter(object):

    def __init__(self, db, entries):
        self.db = db
        self.entries = entries

    def write(self):
        for entry in self.entries:
            thumbnail = entry.thumbnail
            title = entry.title
            link = entry.link
            description = entry.description
            date_published = entry.date_published

            print_entry(entry.__dict__)


def fetch(db, parser, day_limit):
    """
    fetch time is used to not spam servers every time you refresh anything
    """
    session = db.session_factory()
    q = session.query(EntriesTable)
    print("")

    c = SourcesTableController(db)
    sources = session.query(SourcesTable).filter(SourcesTable.enabled == True).all()

    for source in sources:
        date_now = DateUtils.get_datetime_now_utc()
        date_now = date_now.replace(tzinfo=None)

        if not parser.args.force:
           operational_data = SourceOperationalDataController(db, session)
           if not operational_data.is_fetch_possible(source, date_now, 60 * 10):

               if parser.args.verbose:
                   op_data = session.query(SourceOperationalData).filter(SourceOperationalData.source_obj_id == source.id).all()
                   if len(op_data) > 0:
                       print("Source {} does not require fetch yet {}".format(source.title, op_data[0].date_fetched))
                   else:
                       print("Source {} does not require fetch yet?".format(source.title))
               continue

        date_now = DateUtils.get_datetime_now_utc()
        date_now = date_now.replace(tzinfo=None)
        op_con = SourceOperationalDataController(db, session)
        op_con.set_fetched(source, date_now)

        print("\rReading {}".format(source.url), end="")
        source_entries = read_source(db, source)

        for entry in source_entries:
            now = datetime.now(timezone.utc)
            limit = now - timedelta(days = day_limit)

            entires_num = session.query(EntriesTable).filter(EntriesTable.link == entry["link"]).count()

            if entry['date_published'] > limit and entires_num == 0:
                ec = EntriesTableController(db, session)
                ec.add_entry(entry)

        q = session.query(EntriesTable)
        print("Number of entries:{}".format(q.count()))


async def fetch_async(db, parser, day_limit):
    """
    Async version is faster than sequentially asking all sites.
    fetch time is used to not spam servers every time you refresh anything
    """
    print("")
    session = db.session_factory()

    sources = session.query(SourcesTable).all()

    threads = []
    for source in sources:
        date_now = DateUtils.get_datetime_now_utc()
        date_now = date_now.replace(tzinfo=None)

        if not parser.args.force:
            operational_data = SourceOperationalDataController(db, session)
            if not operational_data.is_fetch_possible(source, date_now, 60 * 10):
                if parser.args.verbose:
                    op_data = session.query(SourceOperationalData).filter(SourceOperationalData.source_obj_id == source.id).all()
                    if len(op_data) > 0:
                        print("Source {} does not require fetch yet {}".format(source.title, op_data[0].date_fetched))
                    else:
                        print("Source {} does not require fetch yet?".format(source.title))
                continue

        date_now = DateUtils.get_datetime_now_utc()
        date_now = date_now.replace(tzinfo=None)

        op_con = SourceOperationalDataController(db, session)
        op_con.set_fetched(source, date_now)

        print("\rReading:{}".format(source.title), end="")

        thread = asyncio.to_thread(read_source, db, source)
        threads.append(thread)

    results = await asyncio.gather(*threads)

    total_added_entries = 0

    for result in results:
        for entry in result:
            now = datetime.now(timezone.utc)
            limit = now - timedelta(days = day_limit)

            entires_num = session.query(EntriesTable).filter(EntriesTable.link == entry["link"]).count()

            if entry['date_published'] > limit and entires_num == 0:
                ec = EntriesTableController(db, session)
                ec.add_entry(entry)
                total_added_entries += 1

    print(f"Added {total_added_entries}")

    q = session.query(EntriesTable)
    print("Number of entries:{}".format(q.count()))


def show_stats(db):
    session = db.session_factory()

    q = session.query(EntriesTable)
    count_entries = q.count()

    q = session.query(SourcesTable)
    count_sources = q.count()

    print(f"Entires:{count_entries}")
    print(f"Sources:{count_sources}")


def follow_url(db, page_url):
    def is_source(page_url):
        session = db.session_factory()

        sources = session.query(SourcesTable).filter(SourcesTable.url == page_url).all()
        if len(sources) != 0:
            return True

    source = {}

    if is_source(page_url):
        print("Such source is already added")
        return True

    url = Url.find_rss_url(page_url)
    if not url:
        print("That does not seem to be a correct RSS source:{}".format(page_url))

    response = url.get_response()
    title = url.get_title()

    if not title:
        title = input("Specify title of URL")

    source["url"] = url.url
    source["title"] = title

    if is_source(url.url):
        print("Such source is already added")

    session = db.session_factory()
    session.add( SourcesTable(url = url.url, title = title))
    session.commit()

    print("You started following {}/{}".format(url.url, title))

    return True


def unfollow_url(db, url):
    session = db.session_factory()
    sources = session.query(SourcesTable).filter(SourcesTable.url == url).all()

    for source in sources:
        source.delete()

    session.commit()

    print("You stopped following {}".format(url))

    return True


def source_enable(db, session, source):
    if source.enabled == True:
        return False

    source.enabled = True

    session.commit()

    return True


def source_disable(db, session, source):
    if source.enabled == False:
        return False

    source.enabled = False

    session.commit()

    return True


def add_init_sources(db, sources):
    session = db.session_factory()

    for source in sources:
        sources = session.query(SourcesTable).filter(SourcesTable.url == source["url"]).all()
        if len(sources) == 0:
            print("Adding: {}".format(source["title"]))

            obj = SourcesTable(url = source["url"],
                    title = source["title"])
            session.add(obj)
            session.commit()


def list_sources(db):
    session = db.session_factory()

    sources = session.query(SourcesTable).all()

    for source in sources:
        print_source(source)


class FeedClientParser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(
           description="""RSS feed program. """,
        )
        self.parser.add_argument(
            "--timeout", default=10, type=int, help="Timeout expressed in seconds"
        )
        self.parser.add_argument("--port", type=int, default=0, help="Port, if using web scraping server")
        self.parser.add_argument("-o", "--output-dir", help="HTML output directory")
        self.parser.add_argument("--entry", help="Select entry by ID")
        self.parser.add_argument("--source", help="Select source by ID")
        self.parser.add_argument("-r", "--refresh-on-start", action="store_true", help="Refreshes links, fetches on start")
        self.parser.add_argument("--force", action="store_true", help="Force refresh")
        self.parser.add_argument("--stats", action="store_true", help="Show table stats")
        self.parser.add_argument("--cleanup", action="store_true", help="Remove unreferenced items")
        self.parser.add_argument("--follow", help="Follows specific source")
        self.parser.add_argument("--unfollow", help="Unfollows specific source")
        self.parser.add_argument("--enable", help="Enables specific source")
        self.parser.add_argument("--disable", help="Disables specific source")
        self.parser.add_argument("--list-entries", action="store_true", help="Prints data to stdout")
        self.parser.add_argument("--list-sources",action="store_true", help="Lists sources")
        self.parser.add_argument("--init-sources",action="store_true", help="Initializes sources")
        self.parser.add_argument("--page-details", help="Shows page details for specified URL")
        self.parser.add_argument("--search", help="""Search entries. Example: --search "title=Elon" """)
        self.parser.add_argument("-v", "--verbose",action="store_true", help="Verbose")
        self.parser.add_argument("--db", default="feedclient.db", help="SQLite database file name")

        # TODO implement
        # --since "2024-01-01 12:03

        self.args = self.parser.parse_args()


class SearchResultHandler(AlchemyRowHandler):
    def __init__(self):
        super().__init__()

    def handle_row(self, row):
        print_entry(row)


def get_entries(session, source_id=None):
    query = session.query(EntriesTable)

    if source_id:
        query = query.filter(EntriesTable.source_obj__id == source_id)

    query = query.order_by(desc(EntriesTable.date_published))

    return query.all()


class FeedClient(object):
    def __init__(self, sources = None, day_limit = 7, engine = None):
        self.sources = sources
        self.day_limit = day_limit
        self.engine = engine

        self.parser = FeedClientParser()
        self.parser.parse()

    def run(self):
        database_file = self.parser.args.db

        db = SqlModel(database_file=database_file, engine=self.engine)

        if self.parser.args.init_sources:
            if self.sources and len(self.sources) > 0:
                add_init_sources(db, self.sources)

        if self.parser.args.cleanup:
            db.entries_table.truncate()

        if self.parser.args.follow:
            if not follow_url(db, self.parser.args.follow):
                print("Cannot follow {}".format(self.parser.args.follow))

        if self.parser.args.unfollow:
            unfollow_url(db, self.parser.args.unfollow)

        if self.parser.args.enable:
            c = SourcesTableController(db)
            source = c.get(id = self.parser.args.enable)
            if source:
                if source_enable(db, c.get_session(), source):
                    print("Source was enabled")
                else:
                    print("Cannot enable {}".format(self.parser.args.enable))
            else:
                print("Source does not exist")

        if self.parser.args.disable:
            c = SourcesTableController(db)
            source = c.get(id = self.parser.args.disable)
            if source:
                if source_disable(db, c.get_session(), source):
                    print("Source was disabled")
                else:
                    print("Cannot disable source")
            else:
                print("Source does not exist")

        # one of the below needs to be true
        if self.parser.args.refresh_on_start:
            c = EntriesTableController(db)
            c.remove(self.day_limit)

            #fetch(db, self.parser, self.day_limit)
            asyncio.run(fetch_async(db, self.parser, self.day_limit))
            date_now = DateUtils.get_datetime_now_utc()
            print("Current time:{}".format(date_now))

        if self.parser.args.list_sources:
            list_sources(db)

        if self.parser.args.stats:
            show_stats(db)

        if self.parser.args.output_dir:
            directory = Path(self.parser.args.output_dir)
            if not directory.exists():
                directory.mkdir(parents=True, exist_ok=True)
            else:
                shutil.rmtree(str(directory))
                directory.mkdir(parents=True, exist_ok=True)

            session = db.session_factory()
            entries = get_entries(session, self.parser.args.source)

            verbose = False
            if self.parser.args.verbose:
                verbose = True

            w = HtmlExporter(directory, entries, verbose = verbose)
            w.write()

        if self.parser.args.search:
            s = AlchemySearch(db, self.parser.args.search, row_handler = SearchResultHandler())
            s.search()

        if self.parser.args.page_details:
            from utils.serializers import PageDisplay
            PageDisplay(self.parser.args.page_details, verbose = self.parser.args.verbose)

        if self.parser.args.list_entries:
            session = db.session_factory()
            entries = get_entries(session, self.parser.args.source)

            w = OutputWriter(db, entries)
            w.write()
