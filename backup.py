"""
POSTGRES backup script.

 - Creates and restores backups.
 - Check against data corruption with analyze, vacuum and reindex

What to do:
 - run vacuum, which shows problems with data
 - if any table is affected run reindex on it
 - run reindex from time to time
"""
import sys
import os
import subprocess
import argparse
from pathlib import Path
import time
from datetime import datetime

from sqlalchemy import create_engine, Column, String, Integer, MetaData, Table, text, LargeBinary, DateTime, select
from sqlalchemy.dialects.postgresql.types import BYTEA
from sqlalchemy.orm import sessionmaker

from utils import ReflectedTable

from workspace import get_workspaces


parent_directory = Path(__file__).parents[1]


tables_to_backup = [
  "credentials",
  "sourcecategories",
  "sourcesubcategories",
  "sourcedatamodel",
  "userconfig",
  "configurationentry",
  "linkdatamodel",
  "domains",
  "usertags",
  "compactedtags",
  "usercompactedtags",
  "entrycompactedtags",
  "uservotes",
  "browser",
  "entryrules",
  "dataexport",
  "gateway",
  "modelfiles",
  "readlater",
  "searchview",
  "socialdata",
  # "blockentry", # do not backup it, the list has to be reinitialized each time
  "blockentrylist",
  "usercomments",
  "userbookmarks",
  "usersearchhistory",
  "userentrytransitionhistory",
  "userentryvisithistory",
]


all_tables = list(tables_to_backup)
all_tables.append("blockentry")
all_tables.append("apikeys")
all_tables.append("applogging")
all_tables.append("backgroundjob")
all_tables.append("backgroundjobhistory")
all_tables.append("keywords")

def get_backup_directory(export_type):
    return parent_directory / "data" / ("backup_" + export_type)


def get_workspace_backup_directory(export_type, workspace):
    return get_backup_directory(export_type) / workspace


def run_pg_dump_backup(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    output_file = run_info["output_file"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    if "format" not in run_info:
        run_info["format"] = "custom"

    if run_info["format"] == "custom":
        format_args = "c"
    elif run_info["format"] == "plain" or run_info["format"] == "sql":
        format_args = "p"

    command_input = [
        "pg_dump",
        "-h", host,
        "-U", user,
        "-d", database,
        "-F", format_args,
        "-f", output_file,
        "--data-only",
    ]

    if "format" in run_info and run_info["format"] == "sql":
        command_input.append("--inserts")

    for table in tables:
        command_input.append("-t")
        command_input.append(table)

    operating_dir = get_workspace_backup_directory(run_info["format"], workspace)
    operating_dir.mkdir(parents=True, exist_ok=True)

    print("Running: {} @ {}".format(command_input, operating_dir))

    try:
        result = subprocess.run(command_input, cwd=str(operating_dir), check=True, 
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("Backup completed successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        print("Standard Output:", e.stdout)
        print("Standard Error:", e.stderr)
        return False

    return True


def truncate_table(run_info, table):
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]
    tables = run_info["tables"]

    print("Truncating {}".format(table))

    sql = f'TRUNCATE TABLE {table} CASCADE;'

    command = [
       'psql',
       "-h", host,
       "-U", user,
       "-d", database,
       '-c', sql,
    ]

    try:
        subprocess.run(command, check=True)
        print("Table truncated successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


def reset_table_index_sequence(run_info, table):
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]
    tables = run_info["tables"]

    print("Resetting sequence for table {}".format(table))

    sql = f"SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1));"

    command = [
       'psql',
       "-h", host,
       "-U", user,
       "-d", database,
       '-c', sql,
    ]

    try:
        subprocess.run(command, check=True)
        print("Reset index sequence successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


def reset_tables_index_sequence(tablemapping, run_info):
    workspace = run_info["workspace"]

    # after restore we need to reset sequences
    for item in tablemapping:
        key = item[0]
        tables = item[1]

        run_info["output_file"] = key
        run_info["tables"] = tables

        for table in tables:
            table = table.replace("instance_", workspace+"_")

            if not reset_table_index_sequence(run_info, table):
                print("Could not reset index in table")
                return False

    return True


def run_table_sql(run_info, table, sql):
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    print("Call {} initiating".format(table))

    command = [
       'psql',
       "-h", host,
       "-U", user,
       "-d", database,
       '-c', sql,
    ]

    try:
        subprocess.run(command, check=True)
        print("Call {} successful.".format(sql))
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


def truncate_all(run_info):
    workspace = run_info["workspace"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]
    tables = run_info["tables"]

    for table in tables:
        table = table.replace("instance_", workspace+"_")

        if not truncate_table(run_info, table):
            return False

    return True


def run_pg_restore(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    output_file = run_info["output_file"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    if "format" not in run_info:
        run_info["format"] = "custom"

    if run_info["format"] == "custom":
        format_args = "c"
    elif run_info["format"] == "plain":
        format_args = "p"

    command_input = [
        "pg_restore",
        "-h", host,
        "-U", user,
        "-d", database,
        "-F", format_args,
        "--data-only",
        output_file,
    ]

    for table in tables:
        command_input.append("-t")
        command_input.append(table)

    operating_dir = get_workspace_backup_directory(run_info["format"], workspace)
    operating_dir.mkdir(parents=True, exist_ok=True)

    print("Running: {} @ {}".format(command_input, operating_dir))

    try:
        subprocess.run(command_input, cwd = str(operating_dir), check=True)
        print("Restore completed successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


### SQLite code

def create_destionation_table(table_name, source_table, destination_engine):
    """
    Copy columns from postgres to sqlite
    BYTEA is not represented in sqlite
    """
    with destination_engine.connect() as connection:
        if not destination_engine.dialect.has_table(connection, table_name):
            columns = []
            for column in source_table.columns:
                col_type = column.type
                if isinstance(col_type, BYTEA):
                    col_type = LargeBinary

                # Handle 'id' as primary key and autoincrement in SQLite
                if column.name == "id":
                    columns.append(Column(
                        "id",
                        Integer,
                        primary_key=True,
                        autoincrement=True,
                        nullable=False
                    ))
                else:
                    columns.append(Column(
                        column.name,
                        col_type,
                        nullable=column.nullable
                    ))

                # For debugging purposes, you can print column details
                # print(column.name)
                # print(column.type.__class__)
                # print(f"Nullable: {column.nullable}")

            destination_metadata = MetaData()
            destination_table = Table(table_name, destination_metadata, *columns)
            destination_table.create(destination_engine)


def get_engine_table(workspace, table_name, engine, with_workspace=True):
    if with_workspace:
        this_tables_name = "{}_{}".format(workspace, table_name)
    else:
        this_tables_name = table_name

    engine_metadata = MetaData()
    engine_table = Table(this_tables_name, engine_metadata, autoload_with=engine)
    return engine_table


def get_table_row_values(row, source_table):
    data = {}
    
    for column in source_table.columns:
        value = getattr(row, column.name)
        data[column.name] = value

    return data


def is_row_with_id(connection, table, id_value):
    try:
        existing = connection.execute(
            select(table.c.id).where(table.c.id == id_value)
        ).first()

        return existing
    except Exception as E:
        connection.rollback()
        return False


def copy_table(instance, table_name, source_engine, destination_engine, override=False, to_sqlite=True, commit_every_row=False):
    """
    Copies table from postgres to destination
    @param override If true, will work faster, since it does not check if row with id exists
    @param to_sqlite If to SQLlite then destination table names will not include workspace. If from SQLite then
                  source tables will not include
    """
    Session = sessionmaker(bind=source_engine)
    session = Session()

    source_table = get_engine_table(instance, table_name, source_engine, with_workspace=to_sqlite)
    destination_table = get_engine_table(instance, table_name, destination_engine, with_workspace=not to_sqlite)

    print(f"Copying from {source_table} to {destination_table}")

    with destination_engine.connect() as destination_connection:
        with source_engine.connect() as connection:
            result = connection.execute(source_table.select())

            index = 0
            for row in result:
                index += 1
                sys.stdout.write("{}\r".format(index))

                data = get_table_row_values(row, source_table)

                # Check if the ID already exists
                if not override:
                    id_value = data.get("id")
                    if id_value is not None:
                        existing = is_row_with_id(destination_connection, destination_table, id_value)

                        if existing:
                            continue
                
                try:
                   destination_connection.execute(destination_table.insert(), data)
                except Exception as e:
                    print(f"Skipping row {index} due to insert error {e}")
                    destination_connection.rollback()
                    continue

                if commit_every_row:
                    try:
                        destination_connection.commit()
                    except Exception as e:
                        print(f"Skipping row {index} due to insert error {e}")
                        destination_connection.rollback()
                        continue

            if not commit_every_row:
                destination_connection.commit()

    session.close()


def obfuscate_user_table(table_name, destination_engine):
    """
    Remove passwords from the database
    """
    destination_metadata = MetaData()
    destination_table = Table(table_name, destination_metadata, autoload_with=destination_engine)

    columns = destination_table.columns.keys()
    is_superuser_index = columns.index('is_superuser')

    with destination_engine.connect() as destination_connection:
        result = destination_connection.execute(destination_table.select())

        for row in result:
            update_stmt = destination_table.update().where(destination_table.c.id == row[0]).values(password='')
            destination_connection.execute(update_stmt)

            if is_superuser_index and row[is_superuser_index]:
                update_stmt = destination_table.update().where(destination_table.c.id == row[0]).values(username='admin')

        destination_connection.commit()


def create_indexes(destination_engine, table_name, column_name):
    destination_metadata = MetaData()
    destination_table = Table(table_name, destination_metadata, autoload_with=destination_engine)

    r = ReflectedTable(destination_engine)
    #r.create_index(destination_table, "link")
    #r.create_index(destination_table, "title")
    #r.create_index(destination_table, "date_published")


def obfuscate_all(destination_engine):
    r = ReflectedTable(destination_engine)
    obfuscate_user_table("user", destination_engine)
    r.truncate_table("dataexport")
    r.truncate_table("usersearchhistory")
    r.truncate_table("credentials")


#### SQLite


def get_local_engine(run_info):
    workspace = run_info["workspace"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]
    password = run_info["password"]

    # Create the database engine
    SOURCE_DATABASE_URL = f"postgresql://{user}:{password}@{host}/{database}"
    source_engine = create_engine(SOURCE_DATABASE_URL)

    return source_engine


def get_sqlite_engine(run_info):
    workspace = run_info["workspace"]

    file_name = workspace+".db"
    DESTINATION_DATABASE_URL = "sqlite:///" + file_name
    destination_engine = create_engine(DESTINATION_DATABASE_URL)

    return destination_engine


def run_db_copy_backup(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    empty = run_info["empty"]

    # Create the database engine
    source_engine = get_local_engine(run_info)

    operating_dir = get_workspace_backup_directory(run_info["format"], workspace)
    operating_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(operating_dir)

    destination_engine = get_sqlite_engine(run_info)

    for table in tables:
        table = table.replace(workspace + "_", "")

        source_table = get_engine_table(workspace, table, source_engine)
        create_destionation_table(table, source_table, destination_engine)

        if not empty:
            copy_table(workspace, table, source_engine, destination_engine, override=True, to_sqlite=True)

    return True


def run_db_copy_restore(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    empty = run_info["empty"]
    append = run_info["append"]

    destination_engine = get_local_engine(run_info)

    operating_dir = get_workspace_backup_directory(run_info["format"], workspace)
    os.chdir(operating_dir)

    source_engine = get_sqlite_engine(run_info)

    for table in tables:
        table = table.replace(workspace + "_", "")
        copy_table(workspace, table, source_engine, destination_engine, override=False, to_sqlite=False, commit_every_row=True)

    return True


def run_db_copy_backup_auth(run_info):
    workspace = run_info["workspace"]

    # Create the database engine
    source_engine = get_local_engine(run_info)

    operating_dir = get_workspace_backup_directory(run_info["format"], workspace)
    operating_dir.mkdir(parents=True, exist_ok=True)
    os.chdir(operating_dir)

    destination_engine = get_sqlite_engine(run_info)

    source_table = get_engine_table("auth", "user", source_engine)
    create_destionation_table("user", source_table, destination_engine)

    copy_table("auth", "user", source_engine, destination_engine, override=True, to_sqlite=True)

    return True


def backup_workspace(run_info):
    """
    @note table order is important

    mapping:
      file : tables
    """
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    workspace = run_info["workspace"]

    for table in tables_to_backup:
        new_run_info = dict(run_info)
        new_key = "instance_" + table

        new_run_info["tables"] = []
        new_run_info["output_file"] = new_key

        table_name = workspace + "_" + table
        new_run_info["tables"].append(table_name)

        if new_run_info["format"] == "sqlite":
            if not run_db_copy_backup(new_run_info):
                return False
        else:
            if not run_pg_dump_backup(new_run_info):
                return False

    if run_info["format"] == "custom":
        new_run_info = dict(run_info)
        new_run_info["tables"] = ['auth_user']
        new_run_info["workspace"] = 'auth'
        new_run_info["output_file"] = "auth_user"
        if not run_pg_dump_backup(new_run_info):
            return False

    if run_info["format"] == "sqlite":
        run_db_copy_backup_auth(run_info)

        destination_engine = get_sqlite_engine(run_info)

        create_indexes(destination_engine, "linkdatamodel", "link")
        create_indexes(destination_engine, "linkdatamodel", "title")
        create_indexes(destination_engine, "linkdatamodel", "date_published")

        obfuscate_all(destination_engine)

    return True


def restore_workspace(run_info):
    """
    @note table order is important
    """
    workspace = run_info["workspace"]

    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    if not run_info["append"]:
        for table in tables_to_backup:
            key = "./instance_" + table
            tables = [workspace + "_" + table]

            run_info["output_file"] = key
            run_info["tables"] = tables

            if not truncate_all(run_info):
                print("Could not truncate table")
                return

    for table in tables_to_backup:
        key = "./instance_" + table
        tables = [workspace + "_" + table]

        new_run_info = dict(run_info)

        new_key = key.replace("instance", workspace)
        new_run_info["output_file"] = new_key
        new_run_info["tables"] = []

        for item in tables:
            table_name = item.replace("instance", workspace)
            new_run_info["tables"].append(table_name)

        if new_run_info["format"] == "sqlite":
            if not run_db_copy_restore(new_run_info):
                return False
        else:
            if not run_pg_restore(new_run_info):
                return False

    reset_tables_index_sequence(tablemapping, run_info)

    return True


def run_sql_for_workspaces(run_info, sql_command):
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    workspace = run_info["workspace"]

    for table in all_tables:
        call_table = workspace + "_" + table
        call_sql_command = sql_command.replace("{table}", call_table)

        if not run_table_sql(run_info, call_table, call_sql_command):
            return False

    return True


def parse_backup():
    parser = argparse.ArgumentParser(prog="Backup", description="Backup manager. Please provide .pgpass file, and define your password there.")

    parser.add_argument("-b", "--backup", action="store_true", help="Perform a backup")
    parser.add_argument("-r", "--restore", action="store_true", help="Restore from a backup")
    parser.add_argument("-a", "--analyze", action="store_true", help="Analyze the database")
    parser.add_argument("--vacuum", action="store_true", help="Vacuum the database")
    parser.add_argument("--reindex", action="store_true", help="Reindex the database. Useful to detect errors in consistency")
    parser.add_argument("-s", "--sequence-update", action="store_true", help="Updates sequence numbers")
    parser.add_argument("-U", "--user", default="user", help="Username for the database (default: 'user')")
    parser.add_argument("-d", "--database", default="db", help="Database name (default: 'db')")
    parser.add_argument("-p", "--password", default="", help="Password. Necessary for sqlite format")
    parser.add_argument("-w", "--workspace", help="Workspace for which to perform backup/restore. If not specified - all")
    parser.add_argument("-D", "--debug", help="Enable debug output")  # TODO implement debug
    parser.add_argument("-i", "--ignore-errors", action="store_true", help="Ignore errors during the operation")
    parser.add_argument("--empty", action="store_true", help="Creates empty table version during backup")
    parser.add_argument("--append", action="store_true", help="Appends data during restore, does not clear tables")
    parser.add_argument("-f", "--format", default="custom", choices=["custom", "plain", "sql", "sqlite"],
                        help="Format of the backup (default: 'custom'). Choices: 'custom', 'plain', or 'sql'.")

    parser.add_argument("--host", default="127.0.0.1", help="Host address for the database (default: 127.0.0.1)")

    return parser, parser.parse_args()


def main():
    parser, args = parse_backup()

    if not args.backup and not args.restore and not args.analyze and not args.vacuum and not args.reindex and not args.sequence_update:
        parser.print_help()

    workspaces = []

    if args.workspace:
        all = sorted(list(get_workspaces()))
        if args.workspace not in all:
            answer = input("No such workspace! Do you want to make the export?")
            if answer != "y":
                return

        workspaces = [args.workspace]
    else:
        workspaces = get_workspaces()

    start_time = time.time()

    errors = False

    for workspace in workspaces:
        run_info = {}
        run_info["workspace"] = workspace
        run_info["user"] = args.user
        run_info["database"] = args.database
        run_info["host"] = args.host
        run_info["format"] = args.format
        run_info["password"] = args.password
        run_info["empty"] = args.empty
        run_info["append"] = args.append

        if args.ignore_errors:
            run_info["ignore_errors"] = True

        if args.backup and not backup_workspace(run_info):
            print("Leaving because of errors")
            errors = True
            break

        if args.restore and not restore_workspace(run_info):
            print("Leaving because of errors")
            errors = True
            break

        if args.analyze and not run_sql_for_workspaces(run_info, "ANALYZE {table};"):
            print("Leaving because of errors")
            errors = True
            break

        if args.vacuum and not run_sql_for_workspaces(run_info, "VACUUM {table};"):
            print("Leaving because of errors")
            errors = True
            break

        if args.reindex and not run_sql_for_workspaces(run_info, "REINDEX TABLE {table};"):
            print("Leaving because of errors")
            errors = True
            break

        sql_text = "SELECT setval('{table}_id_seq', COALESCE((SELECT MAX(id) FROM {table}), 1));"
        if args.sequence_update and not run_sql_for_workspaces(run_info, sql_text):
            print("Leaving because of errors")
            errors = True
            break

    if errors:
        print("There were errors")
    else:
        print("All calls were successful")

    elapsed_time_seconds = time.time() - start_time
    elapsed_minutes = int(elapsed_time_seconds // 60)
    elapsed_seconds = int(elapsed_time_seconds % 60)
    print(f"Time: {elapsed_minutes}:{elapsed_seconds}")


if __name__ == "__main__":
    main()
