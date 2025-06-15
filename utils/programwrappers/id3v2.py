import logging
import subprocess
import os


class Id3v2(object):
    def __init__(self, file_name, data=None, cwd=None, timeout_s=60 * 60):
        self.file_name = file_name
        self.timeout_s = timeout_s
        self.data = data
        self.cwd = cwd

    def tag(self):
        if not os.path.splitext(self.file_name)[1] == ".mp3":
            logging.error("Cannot tag file, not an mp3 file")
            return

        song = self.data["title"]

        artist = None
        if "artist" in self.data:
            artist = self.data["artist"]
        album = None
        if "album" in self.data:
            artist = self.data["album"]
        track = None
        if "track" in self.data:
            track = self.data["track"]

        artist = str(artist)
        album = str(album)

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
                ],
                cwd=self.cwd,
                timeout=self.timeout_s,
            )
        else:
            subprocess.run(
                ["id3v2", "-t", song, "-a", artist, "-A", album, self.file_name],
                cwd=self.cwd,
                timeout=self.timeout_s,
            )

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(
                ["id3v2"],
                stdout=subprocess.PIPE,
                timeout=10,
            )
        except:
            return False
        return True
