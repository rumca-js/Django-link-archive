"""
This script will create postgres dump for workspaces.
Creating dump instead of export is way faster.

TODO
 add switches for instance, and for table
 backup -i places -t entries

 add restoration
 pg_restore -U "xx" -d "xx" -1
"""
import subprocess
import argparse
from pathlib import Path

from workspace import get_workspaces


parent_directory = Path(__file__).parents[1]


def run_command(run_info):
    workspace = run_info["workspace"]
    tables = run_info["tables"]
    output_file = run_info["output_file"]
    user = run_info["user"]
    database = run_info["database"]
    host = run_info["host"]

    command_input = [
        "pg_dump",
        "-h", host,
        "-U", user,
        "-d", database,
        "-F", "c",
        "-f", output_file,
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
        print("Backup completed successfully.")
    except subprocess.CalledProcessError as e:
        print("An error occurred:", e)
        return False

    return True


def backup_workspace(run_info):
    print("--------------------")
    print(run_info["workspace"])
    print("--------------------")

    tablemapping = {
       "./instance_entries"   : ["instance_linkdatamodel", "instance_domains"],
       "./instance_sources"   : ["instance_sourcedatamodel"],
       "./instance_tags"      : ["instance_usertags", "instance_compactedtags", "instance_usercompactedtags"],
       "./instance_votes"     : ["instance_uservotes"],
       "./instance_comments"  : ["instance_usercomments"],
       "./instance_userbookmarks" : ["instance_userbookmarks"],
       "./instance_history"   : ["instance_usersearchhistory", "instance_userentrytransitionhistory", "instance_userentryvisithistory"],
    }
    
    for key in tablemapping:
        run_info["output_file"] = key
        run_info["tables"] = tablemapping[key]

        if not run_command(run_info):
            return False

    return True


def parse_backup():
    parser = argparse.ArgumentParser(prog="Backup", description="Backup manager")

    parser.add_argument("-U", "--user", default="user")
    parser.add_argument("-d", "--database", default="db")
    parser.add_argument("--host", default="127.0.0.1")

    return parser, parser.parse_args()


def main():
    parser, args = parse_backup()

    workspaces = get_workspaces()
    for workspace in workspaces:
        run_info = {}
        run_info["workspace"] = workspace
        run_info["user"] = args.user
        run_info["database"] = args.database
        run_info["host"] = args.host

        if not backup_workspace(run_info):
            break


if __name__ == "__main__":
    main()
