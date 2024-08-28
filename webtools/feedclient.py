
"""
This is example script about how to use this project as a simple RSS reader
"""
import argparse
import asyncio
from pathlib import Path
import shutil

from utils.sqlmodel import SqlModel
from datetime import timedelta, datetime, timezone

from webtools import (
    PageOptions,
    WebConfig,
    WebLogger,
    PrintWebLogger,
    Url,
    HttpPageHandler,
)
from utils.serializers import HtmlExporter


__version__ = "0.0.2"


def read_source(source):
    result = []

    source_url = source.url
    source_title = source.title

    options = PageOptions()
    options.use_headless_browser = False
    options.use_full_browser = False

    url = Url(url = source_url, page_options = options)
    handler = url.get_handler()
    response = url.get_response()

    if not handler:
        print("##### Cannot obtain handler for:{}".format(source_url))
        return

    if response:
        entries = handler.get_entries()

        if not entries:
            print("##### Cannot obtain entries for:{}".format(source_url))
            return result

        for item in entries:
            item["source"] = source_url
            item["source_title"] = source_title
            result.append(item)

    return result


class OutputWriter(object):

    def __init__(self, db):
        self.db = db

    def write(self):
        entries = self.db.entries_table.select()
        for entry in entries:
            thumbnail = entry.thumbnail
            title = entry.title
            link = entry.link
            description = entry.description
            date_published = entry.date_published

            print("{} {} {}".format(entry.date_published, entry.link, entry.title,))


def fetch(db, day_limit):
    print("Number of entries:{}".format(db.entries_table.count()))

    sources = db.sources_table.select()

    for source in sources:
        print("Reading {}".format(source.url))
        source_entries = read_source(source)

        for entry in source_entries:
            now = datetime.now(timezone.utc)
            limit = now - timedelta(days = day_limit)

            if entry['date_published'] > limit and not db.entries_table.is_entry(entry):
                db.entries_table.add_entry(entry)

        print("Number of entries:{}".format(db.entries_table.count()))

    db.commit()


async def fetch_async(db, day_limit):
    """
    Async version is really really fast
    """
    print("Number of entries:{}".format(db.entries_table.count()))

    sources = db.sources_table.select()

    threads = []
    for source in sources:
        thread = asyncio.to_thread(read_source, source)
        threads.append(thread)

    results = await asyncio.gather(*threads)

    for result in results:
        for entry in result:
            now = datetime.now(timezone.utc)
            limit = now - timedelta(days = day_limit)

            if entry['date_published'] > limit and not db.entries_table.is_entry(entry):
                db.entries_table.add_entry(entry)

    print("Number of entries:{}".format(db.entries_table.count()))

    db.commit()


def show_stats(entries_table, sources_table):
    count_entries = entries_table.count()
    count_sources = sources_table.count()

    print(f"Entires:{count_entries}")
    print(f"Sources:{count_sources}")


def follow_url(db, url):
    source = {}
    u = Url(url=url)
    response = u.get_response()
    title = u.get_title()

    if not title:
        title = input("Specify title of URL")

    source["url"] = url
    source["title"] = title

    if db.sources_table.is_source(source):
        return False

    db.sources_table.add_source(source)
    db.sources_table.commit()
    return True


def unfollow_url(db, url):
    db.sources_table.remove(url)
    db.sources_table.commit()
    return True


def add_init_sources(db, sources):
    for source in sources:
        if not db.sources_table.is_source(source):
            print("Adding source:{}".format(source["title"]))
            db.sources_table.add_source(source)


def list_sources(db):
    sources = db.sources_table.select()
    for source in sources:
        print("Title:{}".format(source.title))
        print("Url:{}".format(source.url))


class FeedClientParser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument(
            "--timeout", default=10, type=int, help="Timeout expressed in seconds"
        )
        self.parser.add_argument("--port", type=int, default=0, help="Port")
        self.parser.add_argument("-o", "--output-dir", help="HTML output directory")
        self.parser.add_argument("--print", help="Print entries to stdout")
        self.parser.add_argument("-r", "--refresh-on-start", action="store_true", help="Refreshes on start")
        self.parser.add_argument("--stats", action="store_true", help="Show statistics")
        self.parser.add_argument("--cleanup", action="store_true", help="Remove unreferenced items")
        self.parser.add_argument("--follow", help="Follows specific url")
        self.parser.add_argument("--unfollow", help="Unfollows specific url")
        self.parser.add_argument("--list-sources",action="store_true", help="Lists sources")
        self.parser.add_argument("--init-sources",action="store_true", help="Initializes sources")
        self.parser.add_argument("-v", "--verbose",action="store_true", help="Verbose")
        self.parser.add_argument("--db", default="feedclient.db", help="SQLite database file")

        # TODO implement
        # --since "2024-01-01 12:03

        self.args = self.parser.parse_args()


class FeedClient(object):
    def __init__(self, sources = None, day_limit = 7):
        self.sources = sources
        self.day_limit = day_limit

        self.parser = FeedClientParser()
        self.parser.parse()

    def run(self):
        database_file = self.parser.args.db

        db = SqlModel(database_file=database_file)

        if self.parser.args.init_sources:
            add_init_sources(db, self.sources)

        db.entries_table.remove(self.day_limit)

        if self.parser.args.cleanup:
            db.entries_table.truncate()

        if self.parser.args.follow:
            if not follow_url(db, self.parser.args.follow):
                print("Cannot follow {}".format(self.parser.args.follow))
            else:
                print("Added {}".format(self.parser.args.follow))

        if self.parser.args.unfollow:
            unfollow_url(db, self.parser.args.unfollow)

        # one of the below needs to be true
        if self.parser.args.refresh_on_start:
            #fetch(db, self.day_limit)
            asyncio.run(fetch_async(db, self.day_limit))


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

            w = HtmlExporter(directory, db.entries_table.select())
            w.write()

        elif self.parser.args.print:
            w = OutputWriter(db)
            w.write()

        db.close()
