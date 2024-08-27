"""
These types represent commonly used elements: link, channel.
"""

import os


def get_ascii_text(text):
    thebytes = text.encode("ascii", "ignore")
    return thebytes.decode()


def fix_path_for_os(file_path, max_path=260, limit=False):
    """
    @param file_path needs to be string

    Windows for example does not allow certain characters in file names
    """
    chars = [
        ">",
        "<",
        ":",
        "|",
        "?",
        "*",
        '"',
        "'",
    ]

    for item in chars:
        file_path = file_path.replace(item, "")

    # remove duplicate white spaces?
    file_path = " ".join(file_path.split())
    file_path = file_path.strip()

    file_path[: max_path - 1]

    return file_path


def get_directory_size_bytes(start_path="."):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size
