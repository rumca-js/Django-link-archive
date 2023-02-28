
import subprocess
import os
import logging
from pathlib import Path

from youtubedlmgr.programwrappers import ytdownloader


# yt-dlp
# https://github.com/yt-dlp/yt-dlp

class YTDLP(ytdownloader.YouTubeDownloader):

    def __init__(self, url):
        super().__init__(url)

    def download_audio(self, file_name):
        ext = Path(file_name).suffix[1:]

        # https://askubuntu.com/questions/630134/how-to-specify-a-filename-while-extracting-audio-using-youtube-dl

        cmds = ['yt-dlp', '-o', file_name, "-x", "--audio-format", ext, '--prefer-ffmpeg', self._url]
        logging.info("Downloading: " + " ".join(cmds))

        proc = subprocess.run(cmds, capture_output=True)

        if proc.returncode != 0:
            return None

        out = self.get_output_ignore(proc)

        return proc

    def download_video(self, file_name):
        ext = self.get_video_ext()

        #cmds = ['yt-dlp', '-f','bestvideo[ext={0}]+bestaudio'.format(ext), self._url ]
        cmds = ['yt-dlp', '-o', file_name, self._url ]
        logging.info("Downloading: " + " ".join(cmds))
        proc = subprocess.run(cmds, capture_output=True)

        if proc.returncode != 0:
            return None

        out = self.get_output_ignore(proc)

        return proc

    def download_data(self, path = None):
        cmds = ['yt-dlp', '--dump-json', self._url ]

        logging.info("Downloading: " + " ".join(cmds) + str(path))

        proc = subprocess.run(cmds, capture_output=True)
        if proc.returncode != 0:
            return None

        print("Process return code: ", proc.returncode)

        out = self.get_output_ignore(proc)
        self._json_data = out.strip()

        if path is not None:
           path.write_text(self._json_data)

        return self._json_data

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(['yt-dlp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            return False
        return True


