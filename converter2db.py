"""
Takes sql input, and creates db.

TODO:
 - solve errors during conversion.
 - table names do not match with data analyzer

maybe read from postgres directly?
"""
import csv
import re
import json
import os
import sys
import shutil
import time
from pathlib import Path


ENTRIES_PER_PAGE = 1000


from sqlalchemy import create_engine, text


create_database_text = text(""" CREATE DATABASE public; """)


linkdatamodel = """
CREATE TABLE public.places_linkdatamodel (
    id bigint NOT NULL,
    link character varying(1000) NOT NULL,
    source_url character varying(2000) NOT NULL,
    title character varying(1000),
    description text,
    thumbnail character varying(1000),
    language character varying(10),
    age integer,
    date_created timestamp with time zone,
    date_published timestamp with time zone NOT NULL,
    date_update_last timestamp with time zone,
    date_dead_since timestamp with time zone,
    permanent boolean NOT NULL,
    bookmarked boolean NOT NULL,
    author character varying(1000),
    album character varying(1000),
    status_code integer NOT NULL,
    page_rating_contents integer NOT NULL,
    page_rating_votes integer NOT NULL,
    page_rating_visits integer NOT NULL,
    page_rating integer NOT NULL,
    domain_id bigint,
    source_id bigint,
    contents_type integer NOT NULL,
    manual_status_code integer,
    body_hash bytea,
    contents_hash bytea,
    date_last_modified timestamp with time zone,
    user_id integer
);
"""


sourcedatamodel = """
CREATE TABLE public.places_sourcedatamodel (
    id bigint NOT NULL,
    url character varying(2000) NOT NULL,
    title character varying(1000) NOT NULL,
    category_name character varying(1000) NOT NULL,
    subcategory_name character varying(1000) NOT NULL,
    export_to_cms boolean NOT NULL,
    remove_after_days integer NOT NULL,
    language character varying(10) NOT NULL,
    favicon character varying(1000),
    fetch_period integer NOT NULL,
    source_type character varying(1000) NOT NULL,
    proxy_location character varying(200) NOT NULL,
    age integer NOT NULL,
    enabled boolean NOT NULL,
    auto_tag character varying(1000) NOT NULL,
    category_id bigint,
    subcategory_id bigint,
    auto_update_favicon boolean NOT NULL
);
"""


domains = """
CREATE TABLE public.places_domains (
    id bigint NOT NULL,
    domain character varying(1000) NOT NULL,
    main character varying(200),
    subdomain character varying(200),
    suffix character varying(20),
    tld character varying(20)
);
"""


sourcecategories = """
CREATE TABLE public.places_sourcecategories (
    id bigint NOT NULL,
    name character varying(1000) NOT NULL
);
"""


sourcesubcategories = """
CREATE TABLE public.places_sourcesubcategories (
    id bigint NOT NULL,
    category_name character varying(1000) NOT NULL,
    name character varying(1000) NOT NULL,
    category_id bigint
);
"""


compactedtags = """
CREATE TABLE public.places_compactedtags (
    id bigint NOT NULL,
    tag character varying(1000) NOT NULL,
    count integer NOT NULL
);
"""


usercompactedtags = """
CREATE TABLE public.places_usercompactedtags (
    id bigint NOT NULL,
    tag character varying(1000) NOT NULL,
    count integer NOT NULL,
    user_id integer
);
"""


usertags = """
CREATE TABLE public.places_usertags (
    id bigint NOT NULL,
    date timestamp with time zone NOT NULL,
    tag character varying(1000) NOT NULL,
    entry_id bigint,
    user_id integer
);
"""


uservotes = """
CREATE TABLE public.places_uservotes (
    id bigint NOT NULL,
    username character varying(1000) NOT NULL,
    vote integer NOT NULL,
    entry_id bigint,
    user_id integer
);
"""

user = """
CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);
"""

user_inserts = """
INSERT INTO public.auth_user (id, password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined) VALUES
(1, '', '2025-01-25 20:46:36.80233+01', true, 'rumpel', '', '', '', true, true, '2024-02-24 21:42:34.496436+01'),
(3, '', NULL, false, 'tosia', '', '', '', false, true, '2024-10-04 16:35:43.92919+02'),
(2, '', '2024-11-24 22:05:20.283911+01', false, 'michal', '', '', '', false, true, '2024-10-04 16:34:35.757821+02'),
(4, '', '2024-11-28 21:14:19.047173+01', false, 'leonard', '', '', '', false, true, '2024-10-04 17:16:19.471095+02'),
(6, '', '2024-12-02 10:35:56.511447+01', false, 'samos', '', '', '', true, true, '2024-12-02 10:30:00+01');
"""


tables = [
        { "create" : linkdatamodel},
        { "create" : sourcedatamodel},
        { "create" : domains},
        { "create" : sourcecategories},
        { "create" : sourcesubcategories},
        { "create" : compactedtags},
        { "create" : usercompactedtags},
        { "create" : usertags},
        { "create" : uservotes},
        { "create" : user},
]


def replace_statement(statement):
    statement = statement.replace("public.places_", "")
    statement = statement.replace("public.auth", "auth")
    return statement


def find_inserts(file_contents):
    # Use a regular expression to match all INSERT statements
    insert_pattern = r"INSERT INTO.*?VALUES.*?\);\n"
    insert_statements = re.findall(insert_pattern, file_contents, re.DOTALL)

    # Print all the matched INSERT statements
    for statement in insert_statements:
        statement = replace_statement(statement)
        yield statement


class RunningChar(object):
    chars = ["\\", "|", "/", "-"]
    index = 0

    @staticmethod
    def write():
        char = RunningChar.chars[RunningChar.index]
        sys.stdout.write("{}\r".format(char))

        RunningChar.index += 1
        if RunningChar.index >= len(RunningChar.chars):
            RunningChar.index = 0


def create_tables(connection):
    for table in tables:
        table_create = table["create"]
        table_create = replace_statement(table_create)
        table_create = text(table_create)

        connection.execute(table_create)


def write_parsed_data():
    file_name = "test.db"

    path = Path(file_name)
    if path.exists():
        path.unlink()

    engine = create_engine("sqlite:///" + file_name)

    # Execute raw SQL with SQLAlchemy
    with engine.connect() as connection:
        create_tables(connection)
        connection.commit()

    with engine.connect() as connection:
        global user_inserts
        user_inserts = replace_statement(user_inserts)
        user_inserts_text = text(user_inserts)
        connection.execute(user_inserts_text)
        connection.commit()

    process_file(engine, "places_entries")
    process_file(engine, "places_sources")
    process_file(engine, "places_domains")
    process_file(engine, "places_sourcecategories")
    process_file(engine, "places_sourcessubcategories")
    process_file(engine, "places_tags")
    process_file(engine, "places_votes")


def process_file(engine, input_file):
    if not Path(input_file).exists():
        print("Coult not open file {}".format(input_file))
        return

    with open(input_file, "r", encoding="utf-8") as file:
        mytext = file.read()

    good = 0
    bad = 0

    with engine.connect() as connection:
        for index, entry in enumerate(find_inserts(mytext)):
            sys.stdout.write("{}/{}\r".format(good,bad))
            #RunningChar.write()
            entry_text = text(entry)
            try:
                connection.execute(entry_text)
                good += 1
            except Exception as E:
                print(entry)
                print(str(E))
                bad += 1
        connection.commit()  # Commit the transaction

    connection.close()


def main():
    start_time = time.time()
    write_parsed_data()

    elapsed_time_seconds = time.time() - start_time
    elapsed_minutes = int(elapsed_time_seconds // 60)
    elapsed_seconds = int(elapsed_time_seconds % 60)

    print(f"Time: {elapsed_minutes}:{elapsed_seconds}")


main()
