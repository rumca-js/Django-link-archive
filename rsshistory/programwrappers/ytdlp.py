import subprocess
import os
import logging
from pathlib import Path

from .ytdownloader import YouTubeDownloader


# yt-dlp
# https://github.com/yt-dlp/yt-dlp

class YTDLP(YouTubeDownloader):

    def __init__(self, url=None, path=None):
        super().__init__(url, path)

    def download_audio(self, file_name):
        ext = Path(file_name).suffix[1:]

        # https://askubuntu.com/questions/630134/how-to-specify-a-filename-while-extracting-audio-using-youtube-dl

        cmds = ['yt-dlp', '-o', file_name, "-x", "--audio-format", ext, '--prefer-ffmpeg', self._url]

        proc = subprocess.run(cmds, cwd=self._path, capture_output=True)

        if proc.returncode != 0:
            return None

        out = self.get_output_ignore(proc)

        return proc

    def download_video(self, file_name):
        # ext = self.get_video_ext()

        # cmds = ['yt-dlp', '-f','bestvideo[ext={0}]+bestaudio'.format(ext), self._url ]
        cmds = ['yt-dlp', '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4', self._url]
        # cmds = ['yt-dlp', '-o', file_name, self._url ]
        logging.info("Downloading: " + " ".join(cmds))
        proc = subprocess.run(cmds, cwd=self._path, capture_output=True)

        if proc.returncode != 0:
            return None

        out = self.get_output_ignore(proc)

        return proc

    def download_data(self, path=None):
        cmds = ['yt-dlp', '--dump-json', str(self._url)]

        print("Downloading: " + " ".join(cmds) + " " + str(path))

        proc = subprocess.run(cmds, capture_output=True)
        if proc.returncode != 0:
            return None

        print("Process return code: ", proc.returncode)

        out = self.get_output_ignore(proc)
        self._json_data = out.strip()

        if path is not None:
            path.write_text(self._json_data)

        return self._json_data

    def get_channel_video_list(self):
        def add_commas(json_text):
            wh = 0
            while True:
                wh = json_text.find("}}", wh + 1)
                if wh > 0:
                    json_text = json_text[:wh + 2] + "," + json_text[wh + 2:]
                else:
                    break
                wh = wh + 1
            return json_text

        import subprocess
        import json
        p = subprocess.run(['yt-dlp', '-j', '--flat-playlist', self._url], capture_output=True)
        json_text = p.stdout.decode("utf-8")
        json_text = json_text.strip()

        json_text = add_commas(json_text)
        json_text = json_text[:-1]
        json_text = "[" + json_text + "]"

        json = json.loads(json_text)

        result = []

        for item in json:
            if "url" in item and item["url"] is not None:
                result.append(item["url"])

        return result

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(['yt-dlp'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            return False
        return True
