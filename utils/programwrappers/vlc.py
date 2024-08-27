import subprocess
import os


class Vlc(object):
    def __init__(self, name, timeout_s=60 * 60):
        self.name = name
        self.timeout_s = timeout_s

    def run(self):
        data = subprocess.run(
            ["vlc", self.name, "vlc://quit"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=self.timeout_s,
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
