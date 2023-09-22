import os, sys
import shutil
from pathlib import Path


def get_source_files(path):
    result_files = []

    for root, dirs, files in os.walk(str(path), topdown=False):
       for name in files:
           file_name = os.path.join(root, name)
           print(file_name)
           result_files.append(Path(file_name))

    return result_files


class FileConverter(object):

    def __init__(self, source_file):
        self.abs_source_file = source_file

    def convert(self, source_app, destination_app):
        destination_abs_file_name = self.get_new_name(source_app, destination_app)

        destination_abs_file_name.parent.mkdir(parents=True, exist_ok=True)

        try:
            original_contents = self.abs_source_file.read_text()
            new_contents = original_contents.replace(source_app, destination_app)
            destination_abs_file_name.write_text(new_contents)

        except Exception as e:
            original_contents = self.abs_source_file.read_bytes()
            destination_abs_file_name.write_bytes(original_contents)


    def get_new_name(self, source_app, destination_app):
        file_name = str(self.abs_source_file)

        destionation_path = file_name.replace(source_app, destination_app)
        return Path(destionation_path)

    def is_ok(self):
        if str(self.abs_source_file).find("__pycache__") >= 0 or \
           str(self.abs_source_file).find("migrations") >= 0:
            return False
        return True


def remove_path(path):
    destination_path = Path(path)
    if destination_path.exists():
        print("Removing old path {}".format(destination_path))
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
    print("Processing app:{}".format(source_app))

    snapshot = Snapshot()
    snapshot.add(Path(destination_app) / "migrations")
    snapshot.add(Path(destination_app) / "static" / destination_app / "icons" )

    remove_path(destination_app)

    source_files = get_source_files(Path(source_app))
    for source_file in source_files:
        conv = FileConverter(source_file)
        if conv.is_ok():
            # print("Converting {}".format(source_file))
            conv.convert(source_app, destination_app)

    snapshot.restore()


def get_workspaces(self):
    result = []
    items_in_dir = os.listdir(".")
    for item in items_in_dir:
        full_path_item = item + "/apps.py"
        if os.path.isfile(full_path_item):
            if item != "private":
                result.append(item)

    return result


def main():
    if len(sys.argv) < 2:
        workspaces = get_workspaces()
        for workspace in workspaces:
            if workspace != "rsshistory":
                update_workspace("rsshistory", workspace)
    else:
        update_workspace("rsshistory", sys.argv[1])


main()

# TODO write celery.py file, autogenerate
