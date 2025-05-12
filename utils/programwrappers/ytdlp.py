import subprocess
import os
import logging
from pathlib import Path

from .ytdownloader import YouTubeDownloader


class YTDLP(YouTubeDownloader):
    """
    yt-dlp Wrapper class
    https://github.com/yt-dlp/yt-dlp
    """

    def __init__(self, url=None, cwd=None, timeout_s=60 * 60):
        """
        Default timeout 1 hour
        """
        super().__init__(url, cwd)
        self.timeout_s = timeout_s

    def download_audio(self, file_name):
        ext = Path(file_name).suffix[1:]

        # https://askubuntu.com/questions/630134/how-to-specify-a-filename-while-extracting-audio-using-youtube-dl

        cmds = [
            "yt-dlp",
            "-o",
            file_name,
            "-x",
            "--audio-format",
            ext,
            "--prefer-ffmpeg",
            self._url,
        ]

        try:
            proc = subprocess.run(
                cmds, cwd=self._cwd, capture_output=True, timeout=self.timeout_s
            )
        except FileNotFoundError as E:
            return

        if proc.returncode != 0:
            return None

        out = self.get_output_ignore(proc)

        return proc

    def download_video(self, file_name):
        cmds = ["yt-dlp", "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/mp4", self._url]

        try:
            proc = subprocess.run(
                cmds, cwd=self._cwd, capture_output=True, timeout=self.timeout_s
            )
        except FileNotFoundError as E:
            return

        if proc.returncode != 0:
            return

        out = self.get_output_ignore(proc)

        return proc

    def download_data(self, path=None):
        cmds = ["yt-dlp", "--dump-json", "--max-downloads", "1", str(self._url)]

        try:
            proc = subprocess.run(cmds, capture_output=True, timeout=self.timeout_s)
        except FileNotFoundError as E:
            return

        out = self.get_output_ignore(proc)

        error = proc.stderr.decode("ascii", errors="ignore")

        # return code 101 is returned due to --max-downloads limit
        # everything is fine

        if proc.returncode != 0 and proc.returncode != 101:
            return

        out = self.get_output_ignore(proc)
        self._json_data = out.strip()

        if path is not None:
            path.write_text(self._json_data)

        return self._json_data

    def get_channel_video_list(self, newest=True):
        """
        TODO
        add argument ascending / descending. Which is default?

        https://www.reddit.com/r/youtubedl/comments/si624k/is_there_any_tool_to_generate_a_list_of_all/

        yt-dlp --print "%(id)s;%(title)s" "URL" > file.csv
        we could also try non json list
        """

        def add_commas(json_text):
            wh = 0
            while True:
                wh = json_text.find("}}", wh + 1)
                if wh > 0:
                    json_text = json_text[: wh + 2] + "," + json_text[wh + 2 :]
                else:
                    break
                wh = wh + 1
            return json_text

        import subprocess
        import json

        """
        How to limit number of items in playlist?
        --playlist-start NUMBER          -I NUMBER:
        --playlist-end NUMBER            -I :NUMBER
        """

        p = subprocess.run(
            ["yt-dlp", "-j", "--flat-playlist", self._url],
            capture_output=True,
            timeout=self.timeout_s,
        )
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

        if newest == True:
            result.reverse()

        return result

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(
                ["yt-dlp"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=10,
            )
        except:
            return False
        return True
