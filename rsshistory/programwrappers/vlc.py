import subprocess
import os


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
