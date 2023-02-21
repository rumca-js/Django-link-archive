
import subprocess
import os
import logging
from pathlib import Path


## Program definitions



# We do not use python youtube interface. It will not work with windows executable.

# youtube-dl.exe --write-description --write-info-json --write-annotations --write-sub --write-thumbnail https://www.youtube.com/watch?v=NlovbLiuGLM&t=433s

# youtube-dl.exe --get-title https://www.youtube.com/watch?v=NlovbLiuGLM
# youtube-dl.exe --get-description https://www.youtube.com/watch?v=NlovbLiuGLM
# youtube-dl.exe --get-filename https://www.youtube.com/watch?v=NlovbLiuGLM
# youtube-dl.exe --dump-json https://www.youtube.com/watch?v=NlovbLiuGLM
# youtube-dl.exe --get-thumbnail https://www.youtube.com/watch?v=NlovbLiuGLM

# youtube-dl.exe --get-title --get-filename --get-description https://www.youtube.com/watch?v=NlovbLiuGLM

# youtube-dl --print-json https://www.youtube.com/playlist?list=<playlist_id> > example.json
# youtube-dl --dump-json https://www.youtube.com/playlist?list=<playlist_id> > example.json

# https://stackoverflow.com/questions/18054500/how-to-use-youtube-dl-from-a-python-program
# https://github.com/ytdl-org/youtube-dl/blob/master/README.md#embedding-youtube-dl


class YouTubeDownloader(object):

    def __init__(self, url):
        self._url = url

    def download_audio(self, file_name):
        ext = Path(file_name).suffix[1:]
        yt_file_name = self.get_audio_file_name()

        # https://askubuntu.com/questions/630134/how-to-specify-a-filename-while-extracting-audio-using-youtube-dl

        cmds = ['youtube-dl', '-o', file_name, "-x", "--audio-format", ext, '--prefer-ffmpeg', self._url]
        logging.info("Downloading: " + " ".join(cmds))
        proc = subprocess.run(cmds, stdout=subprocess.PIPE)

        out = self.get_output_ignore(proc)

        return proc

    def download_video(self, file_name):
        ext = self.get_video_ext(Path(file_name))
        yt_file_name = self.get_video_file_name()

        #cmds = ['youtube-dl','-o', file_name, '-f','bestvideo[ext={0}]+bestaudio'.format(ext), self._url ]
        cmds = ['youtube-dl','-o', file_name, self._url ]
        logging.info("Downloading: " + " ".join(cmds))
        proc = subprocess.run(cmds, stdout=subprocess.PIPE)

        out = self.get_output_ignore(proc)

        return proc

    def save_data(self, file_name):
        data = self.get_json()
        with open(file_name, "w") as fh:
            fh.write(data)

    def get_thumbs_data(self):
        code = self.process_link(self._url)
        url = "https://returnyoutubedislikeapi.com/votes?videoId="+code
        from ..webtools import Page

        data = Page(url).get_contents()
        return data

    def _get_json_data(self):
        proc = subprocess.run(['youtube-dl', '--dump-json', self._url ], stdout=subprocess.PIPE)
        out = self.get_output_ignore(proc)
        self._json_data = out.strip()
        return self._json_data

    def get_json(self):
        json_data = self._get_json_data()

        js = youtubelinkjson.YouTubeJson(json_data)

        thumbs_data = self.get_thumbs_data()
        if not thumbs_data:
            logging.error("Could not obtain returndislikeapi")
            return None

        # TODO - we should only call YouTubeJson to obtain data
        thumbs = returndislikejson.YouTubeThumbsDown(thumbs_data)

        js.add_thumbs_data(thumbs)

        if not js.is_valid():
            logging.error("Data are not valid")
            return None

        return js

    def get_audio_file_name(self):
        js = self.get_json()
        if js:
            file_name = js.get_file_name()

            return os.path.splitext(file_name)[0] + "." + self.get_audio_ext()

    def get_video_file_name(self):
        js = self.get_json()
        if js:
            out = js.get_file_name()

            return os.path.splitext(out)[0] + "." + self.get_video_ext()

    def get_output_ignore(self, proc):
        simple_text = proc.stdout.decode("ascii", errors="ignore")
        return simple_text

    def process_link(self, link):
        wh = link.find("=")
        if wh == -1:
            self._video_code = link
        else:
            wh2 = link.find("&")
            if wh2 != -1:
                self._video_code = link[wh+1:wh2]
            else:
                self._video_code = link[wh+1:]

        return self._video_code

    @staticmethod
    def validate():
        try:
            proc = subprocess.run(['youtube-dl'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except:
            return False
        return True
