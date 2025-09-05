"""
@breif This program manages "workspaces".

Each django app is a "workspace". Each workspace contain separate set of links in the database.

Therefore you can have multiple apps for managing different resources.

For example you can have workspaces like:
     - music
     - movies
     - youtube
     - memes
     - work
     - etc.
"""

import os, sys
import shutil
import importlib
from pathlib import Path
import argparse
import traceback


def get_source_files(path):
    result_files = []

    for root, dirs, files in os.walk(str(path), topdown=False):
        for name in files:
            file_name = os.path.join(root, name)
            result_files.append(Path(file_name))

    return result_files


class FileConverter(object):
    def __init__(self, source_file):
        self.abs_source_file = source_file

    def convert(self, source_app, destination_app):
        destination_abs_file_name = self.get_destination_full_name(
            source_app, destination_app
        )

        destination_abs_file_name.parent.mkdir(parents=True, exist_ok=True)

        try:
            original_contents = self.abs_source_file.read_text()
            new_contents = original_contents.replace(source_app, destination_app)
            destination_abs_file_name.write_text(new_contents)

        except Exception as e:
            original_contents = self.abs_source_file.read_bytes()
            destination_abs_file_name.write_bytes(original_contents)

    def copy(self, source_app, destination_app, overwrite=False):
        destination_abs_file_name = self.get_destination_full_name(
            source_app, destination_app
        )

        if destination_abs_file_name.exists():
            return

        destination_abs_file_name.parent.mkdir(parents=True, exist_ok=True)

        original_contents = self.abs_source_file.read_text()
        destination_abs_file_name.write_text(original_contents)

    def get_destination_full_name(self, source_app, destination_app):
        file_name = str(self.abs_source_file)

        destionation_path = file_name.replace(source_app, destination_app)
        return Path(destionation_path)

    def is_convert_ok(self):
        if (
            str(self.abs_source_file).find("__pycache__") >= 0
            or str(self.abs_source_file).find("migrations") >= 0
        ):
            return False
        return True

    def is_copy_ok(self):
        return str(self.abs_source_file).startswith("prj")


def remove_path(path):
    destination_path = Path(path)
    if destination_path.exists():
        shutil.rmtree(destination_path)


class Snapshot(object):
    def __init__(self):
        self.files_data = []

    def add(self, path):
        if path.exists():
            self.make_snapshot(path)

    def make_snapshot(self, path):
        files = get_source_files(path)
        for afile in files:
            bytes = afile.read_bytes()

            self.files_data.append([afile, bytes])

    def restore(self):
        for file_data in self.files_data:
            file_path = file_data[0]
            file_bytes = file_data[1]

            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_bytes(file_bytes)


def update_workspace(source_app, destination_app):
    print("Processing app:{}".format(destination_app))

    snapshot = Snapshot()
    snapshot.add(Path(destination_app) / "migrations")
    snapshot.add(Path(destination_app) / "static" / destination_app / "icons")

    remove_path(destination_app)

    try:
        source_files = get_source_files(Path(source_app))
        for source_file in source_files:
            conv = FileConverter(source_file)

            if conv.is_convert_ok():
                conv.convert(source_app, destination_app)
            elif conv.is_copy_ok():
                conv.copy(source_app, destination_app)
    except Exception as e:
        print("Exception when trying to copy files {}".format(str(e)))

    snapshot.restore()


def create_workspace(source_app, destination_app):
    print("Processing app:{}".format(destination_app))

    destination_app = Path(destination_app)

    if destination_app.exists():
        return False

    source_files = get_source_files(Path(source_app))
    for source_file in source_files:
        conv = FileConverter(source_file)
        if conv.is_convert_ok():
            conv.convert(source_app, str(destination_app))

    migration_path = destination_app / "migrations"
    migration_path.mkdir(parents=True, exist_ok=True)
    migration_path_file = migration_path / "__init__.py"
    migration_path_file.touch()

    return True


def get_workspaces():
    directory = Path(__file__).parent

    result = []
    items_in_dir = os.listdir(str(directory))
    for item in items_in_dir:
        full_path_item = item + "/apps.py"
        if os.path.isfile(full_path_item):
            result.append(item)

    return result


def parse():
    parser = argparse.ArgumentParser(prog="Workspace", description="Workspace manager")

    parser.add_argument("-c", "--create")
    parser.add_argument("-u", "--update")
    parser.add_argument("-U", "--update-all", action="store_true", dest="update_all")

    return parser, parser.parse_args()


def main():
    parser, args = parse()

    if args.update_all:
        workspaces = get_workspaces()
        for workspace in workspaces:
            if workspace != "rsshistory":
                update_workspace("rsshistory", workspace)

    elif args.update:
        update_workspace("rsshistory", args.update)

    elif args.create:
        if not create_workspace("rsshistory", args.create):
            print("Could not create workspace. Please check if directory exists:{}".format(args.create))
        else:
            print("Call python makemigration & python migrate")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()

# TODO write celery.py file, autogenerate
