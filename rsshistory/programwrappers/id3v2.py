import logging
import subprocess
import os
from ..apps import LinkDatabase


class Id3v2(object):
    def __init__(self, file_name, data=None):
        self.file_name = file_name

        self.data = data

    def tag(self):
        if not os.path.splitext(self.file_name)[1] == ".mp3":
            logging.error("Cannot tag file, not an mp3 file")
            return

        song = self.data["title"]
        artist = self.data["artist"]
        album = self.data["album"]
        track = None
        if "track" in self.data:
            track = self.data["track"]

        LinkDatabase.info(
            "Tagging Song:'{0}' Artist:'{1}' Album:'{2}'".format(song, artist, album)
        )

        if track:
            subprocess.run(
                [
                    "id3v2",
                    "-t",
                    song,
                    "-a",
                    artist,
                    "-A",
                    album,
                    "-T",
                    str(self._track),
                    self.file_name,
                ]
            )
        else:
            subprocess.run(
                ["id3v2", "-t", song, "-a", artist, "-A", album, self.file_name]
            )

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(["id3v2"], stdout=subprocess.PIPE)
        except:
            return False
        return True
