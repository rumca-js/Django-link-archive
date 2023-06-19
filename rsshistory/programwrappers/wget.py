import subprocess
import os
import logging
from pathlib import Path


class Wget(object):

    def __init__(self, url=None, path=None):
        self.url = url
        self.path = path

    def download_all(self):
        cmds = ['wget', '-p', '-k', self.url]

        proc = subprocess.run(cmds, capture_output=True, cwd=self.path)

        if proc.returncode != 0:
            return None
