"""
This script copies data from postgres to a nosql file
"""
from pathlib import Path
from datetime import datetime
import argparse
import time
import sys

from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table, text, LargeBinary, DateTime
from sqlalchemy.dialects.postgresql.types import BYTEA
from sqlalchemy.orm import sessionmaker


def create_destionation_table(table_name, source_table, destination_engine):
    """
    Copy columns from postgres to nosql
    BYTEA is not represented in nosql
    """
    with destination_engine.connect() as connection:
        if not destination_engine.dialect.has_table(connection, table_name):
            columns = []
            for column in source_table.columns:
                # Mapping bytea to LargeBinary (or appropriate type)
                if column.type.__class__ == BYTEA:
                    columns.append(Column(column.name, LargeBinary, nullable=column.nullable))
                else:
                    columns.append(Column(column.name, column.type, nullable=column.nullable))

                # For debugging purposes, you can print column details
                # print(column.name)
                # print(column.type.__class__)
                # print(f"Nullable: {column.nullable}")

            destination_metadata = MetaData()
            destination_table = Table(table_name, destination_metadata, *columns)
            destination_table.create(destination_engine)


def copy_table(instance, table_name, source_engine, destination_engine):
    """
    Copies table from postgres to destination
    """
    Session = sessionmaker(bind=source_engine)
    session = Session()

    # Reflect the table using SQLAlchemy metadata
    source_metadata = MetaData()
    source_table = Table("{}_{}".format(instance, table_name), source_metadata, autoload_with=source_engine)

    print("{} Creating table".format(table_name))
    create_destionation_table(table_name, source_table, destination_engine)

    # Reflect the destination table after ensuring it exists
    destination_metadata = MetaData()
    destination_table = Table(table_name, destination_metadata, autoload_with=destination_engine)

    print("{} Copying table".format(table_name))

    with destination_engine.connect() as destination_connection:
        with source_engine.connect() as connection:
            result = connection.execute(source_table.select())

            index = 0
            for row in result:
                index += 1

                data = {}
                
                for column in source_table.columns:
                    value = getattr(row, column.name)
                    data[column.name] = value
                
                destination_connection.execute(destination_table.insert(), data)

                sys.stdout.write("{}\r".format(index))

            destination_connection.commit()

    session.close()


def parse_input():
    parser = argparse.ArgumentParser(prog="Backup", description="Backup manager. Please provide .pgpass file, and define your password there.")

    parser.add_argument("-U", "--user", default="user", help="Username for the database (default: 'user')")
    parser.add_argument("-p", "--password", default="", help="Password for the database")
    parser.add_argument("-d", "--database", default="db", help="Database name (default: 'db')")
    parser.add_argument("-w", "--workspace", default="places", help="Workspace for which to perform backup/restore. If not specified - all")
    parser.add_argument("--host", default="127.0.0.1", help="Host address for the database (default: 127.0.0.1)")
    parser.add_argument("-o", "--output", default="test.db", help="Output file name (default: 'db')")

    return parser, parser.parse_args()


def obfuscate(workspace, table_name, destination_engine):
    destination_metadata = MetaData()
    destination_table = Table(table_name, destination_metadata, autoload_with=destination_engine)

    with destination_engine.connect() as destination_connection:
        result = destination_connection.execute(destination_table.select())

        for row in result:
            update_stmt = destination_table.update().where(destination_table.c.id == row[0]).values(password='')
            destination_connection.execute(update_stmt)

        destination_connection.commit()


def main():
    start_time = time.time()

    parser, args = parse_input()

    # Database credentials
    USER = args.user
    PASSWORD = args.password

    HOST = args.host
    DATABASE = args.database

    file_name = args.output

    path = Path(file_name)
    if path.exists():
        path.unlink()

    # Create the database engine
    SOURCE_DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}"
    source_engine = create_engine(SOURCE_DATABASE_URL)

    DESTINATION_DATABASE_URL = "sqlite:///" + file_name
    destination_engine = create_engine(DESTINATION_DATABASE_URL)

    tables = [
        "linkdatamodel",
        "sourdatamodel",
        "domains",
        "sourcecategories",
        "sourcesubcategories",
        "compactedtags",
        "usercompactedtags",
        "usertags",
        "uservotes",
    ]

    workspace = args.workspace

    for table in tables:
        copy_table(workspace, table, source_engine, destination_engine)

    copy_table("auth", "user", source_engine, destination_engine)
    obfuscate("auth", "user", destination_engine)

    elapsed_time_seconds = time.time() - start_time
    elapsed_minutes = int(elapsed_time_seconds // 60)
    elapsed_seconds = int(elapsed_time_seconds % 60)
    print(f"Time: {elapsed_minutes}:{elapsed_seconds}")


main()
