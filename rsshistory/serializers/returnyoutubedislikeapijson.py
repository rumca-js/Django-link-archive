import logging
import json


class YouTubeThumbsDown(object):
    def __init__(self, link=None):
        self._link = link

    def download_data(self):
        return YouTubeThumbsDown.read_code_data(self._link.get_video_code())

    def read_code_data(code):
        from ..pluginurl import UrlHandler

        url = "https://returnyoutubedislikeapi.com/votes?videoId=" + code

        u = UrlHandler(url)
        data = u.get_contents()
        return data

    def loads(self, data):
        try:
            self._json = json.loads(data)
            return self._json
        except Exception as e:
            logging.critical(e, exc_info=True)
            self._json = {}

    def get_json(self):
        return self._json

    def get_thumbs_up(self):
        return self._json["likes"]

    def get_thumbs_down(self):
        return self._json["dislikes"]

    def get_view_count(self):
        return self._json["viewCount"]

    def get_rating(self):
        return self._json["rating"]
