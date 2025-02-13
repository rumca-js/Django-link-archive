"""
POSTGRES backup script.

 - Creates and restores backups.
 - Check against data corruption with analyze, vacuum and reindex

What to do:
 - run vacuum, which shows problems with data
 - if any table is affected run reindex on it
 - run reindex from time to time
"""
import subprocess
import argparse
from pathlib import Path

from workspace import get_workspaces


parent_directory = Path(__file__).parents[1]


def run_backup_command(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    output_file = run_info["output_file"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    format_args = "c"
    if "format" in run_info and (run_info["format"] == "plain" or run_info["format"] == "sql"):
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

    transformed = []
    for item in command_input:
        transformed.append( item.replace("instance_", workspace+"_") )

    operating_dir = parent_directory / "data" / "backup" / workspace

    print("Running: {} @ {}".format(transformed, operating_dir))

    operating_dir.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(transformed, cwd=str(operating_dir), check=True, 
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


def run_restore_command(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    output_file = run_info["output_file"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    format_args = "c"
    if "format" in run_info and run_info["format"] == "plain":
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

    transformed = []
    for item in command_input:
        transformed.append( item.replace("instance_", workspace+"_") )

    operating_dir = parent_directory / "data" / "backup" / workspace

    print("Running: {} @ {}".format(transformed, operating_dir))

    operating_dir.mkdir(parents=True, exist_ok=True)

    try:
        subprocess.run(transformed, cwd = str(operating_dir), check=True)
        print("Restore completed successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


def backup_workspace(run_info):
    """
    @note table order is important
    """
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    tablemapping = {
       "./instance_entries"   : ["instance_linkdatamodel"],
       "./instance_domains"   : ["instance_domains"],
       "./instance_sourcecategories"   : ["instance_sourcecategories"],
       "./instance_sourcessubcategories"   : ["instance_sourcesubcategories"],
       "./instance_sources"   : ["instance_sourcedatamodel"],
       "./instance_tags"      : ["instance_usertags", "instance_compactedtags", "instance_usercompactedtags"],
       "./instance_votes"     : ["instance_uservotes"],
       "./instance_entryrules"     : ["instance_entryrules"],
       "./instance_dataexport"     : ["instance_dataexport"],
       "./instance_gateway"     : ["instance_gateway"],
       "./instance_modelfiles"     : ["instance_modelfiles"],
       "./instance_readlater"     : ["instance_readlater"],
       "./instance_blockentrylist"     : ["instance_blockentrylist"],
       "./instance_comments"  : ["instance_usercomments"],
       "./instance_userbookmarks" : ["instance_userbookmarks"],
       "./instance_history"   : ["instance_usersearchhistory", "instance_userentrytransitionhistory", "instance_userentryvisithistory"],
       "./instance_userconfig" : ["instance_userconfig"],
       "./instance_configurationentry" : ["instance_configurationentry"],
    }

    for key in tablemapping:
        run_info["output_file"] = key
        run_info["tables"] = tablemapping[key]

        if not run_backup_command(run_info):
            return False

    return True


def restore_workspace(run_info):
    """
    @note table order is important
    """
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    # order is important
    tablemapping = [
       ["./instance_sourcecategories"         , ["instance_sourcecategories"]],
       ["./instance_sourcessubcategories"         , ["instance_sourcesubcategories"]],
       ["./instance_sources"         , ["instance_sourcedatamodel"]],
       ["./instance_domains"         , ["instance_domains"]],
       ["./instance_entries"         , ["instance_linkdatamodel"]],
       ["./instance_tags"            , ["instance_usertags", "instance_compactedtags", "instance_usercompactedtags"]],
       ["./instance_votes"           , ["instance_uservotes"]],
       ["./instance_comments"        , ["instance_usercomments"]],
       ["./instance_userbookmarks"   , ["instance_userbookmarks"]],
       ["./instance_entryrules"   , ["instance_entryrules"]],
       ["./instance_dataexport"   , ["instance_dataexport"]],
       ["./instance_gateway"   , ["instance_gateway"]],
       #["./instance_blockentrylist"   , ["instance_blockentrylist"]],
       ["./instance_modelfiles"   , ["instance_modelfiles"]],
       ["./instance_readlater"   , ["instance_readlater"]],
       ["./instance_userconfig"   , ["instance_userconfig"]],
       ["./instance_configurationentry"   , ["instance_configurationentry"]],
       ["./instance_history"         , ["instance_usersearchhistory", "instance_userentrytransitionhistory", "instance_userentryvisithistory"]],
    ]

    for item in tablemapping:
        key = item[0]
        tables = item[1]

        run_info["output_file"] = key
        run_info["tables"] = tables

        if not truncate_all(run_info):
            print("Could not truncate table")
            return

    for item in tablemapping:
        key = item[0]
        tables = item[1]

        run_info["output_file"] = key
        run_info["tables"] = tables

        if not run_restore_command(run_info):
            return False

    return True


def run_sql_for_workspaces(run_info, sql_command):
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    # order is important
    tablemapping = [
       "instance_apikeys",
       "instance_applogging",
       "instance_backgroundjob",
       "instance_blockentry",
       "instance_blockentrylist",
       "instance_browser",
       "instance_configurationentry",
       "instance_domains",
       "instance_dataexport",
       "instance_entryrules",
       "instance_gateway",
       "instance_keywords",
       "instance_linkdatamodel",
       "instance_modelfiles",
       "instance_readlater",
       "instance_sourcecategories",
       "instance_sourcesubcategories",
       "instance_sourcedatamodel",
       "instance_userconfig",
       "instance_usercomments",
       "instance_userbookmarks",
       "instance_usersearchhistory", "instance_userentrytransitionhistory", "instance_userentryvisithistory",
       "instance_usertags", "instance_compactedtags", "instance_usercompactedtags",
       "instance_uservotes",
    ]

    workspace = run_info["workspace"]

    for table in tablemapping:
        call_table = table.replace("instance", workspace)
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
    parser.add_argument("-U", "--user", default="user", help="Username for the database (default: 'user')")
    parser.add_argument("-d", "--database", default="db", help="Database name (default: 'db')")
    parser.add_argument("-w", "--workspace", help="Workspace for which to perform backup/restore. If not specified - all")
    parser.add_argument("-D", "--debug", help="Enable debug output")  # TODO implement debug
    parser.add_argument("-i", "--ignore-errors", action="store_true", help="Ignore errors during the operation")
    parser.add_argument("-f", "--format", default="custom", choices=["custom", "plain", "sql"],
                        help="Format of the backup (default: 'custom'). Choices: 'custom', 'plain', or 'sql'.")

    parser.add_argument("--host", default="127.0.0.1", help="Host address for the database (default: 127.0.0.1)")

    return parser, parser.parse_args()


def main():
    parser, args = parse_backup()

    if not args.backup and not args.restore and not args.analyze and not args.vacuum and not args.reindex:
        parser.print_help()

    workspaces = []

    if args.workspace:
        all = get_workspaces()
        if args.workspace in all:
            workspaces = [args.workspace]
        else:
            print("No such workspace!")
    else:
        workspaces = get_workspaces()


    errors = False

    for workspace in workspaces:
        run_info = {}
        run_info["workspace"] = workspace
        run_info["user"] = args.user
        run_info["database"] = args.database
        run_info["host"] = args.host
        run_info["format"] = args.format
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

    if errors:
        print("There were errors")
    else:
        print("All calls were successful")


if __name__ == "__main__":
    main()
