"""
These types represent commonly used elements: link, channel.
"""

import os


def get_ascii_text(text):
    thebytes = text.encode("ascii", "ignore")
    return thebytes.decode()


def fix_path_for_windows(file_path):
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

    file_path = " ".join(file_path.split())
    file_path = file_path.strip()

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
