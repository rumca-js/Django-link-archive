import subprocess
import os

from ..apps import LinkDatabase


class FFmpeg(object):
    def __init__(self, name):
        self.name = name

    def convert_to_mp3(self, mp3_name):
        LinkDatabase.info("Converting to mp3: {0}".format(mp3_name))

        data = subprocess.run(
            ["ffmpeg", "-y", "-i", self.name, "-vn", mp3_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        os.remove(self.name)

        return mp3_name

    def get_mp3_file_name(self):
        return self.name.replace(".m4a", ".mp3")

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(
                ["ffmpeg"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except:
            return False
        return True


class Vlc(object):
    def __init__(self, name):
        self.name = name

    def run(self):
        data = subprocess.run(
            ["vlc", self.name, "vlc://quit"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(
                ["vlc"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )
        except:
            return False
        return True
