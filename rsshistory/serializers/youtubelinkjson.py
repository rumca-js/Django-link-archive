import os
import json
import logging


class YouTubeJson(object):

    def __init__(self, url = None):
        self._json = {}
        self.url = url

    def get_json_data(self):
        return json.dumps(self._json)

    def is_valid(self):
        return self._json != {}

    def get_json(self):
        return self._json

    def loads(self, data):
        try:
            self._json = json.loads(data)
            return self._json
        except Exception as e:
            logging.critical(e, exc_info=True)

    def write(self, file_name, force = True):
        file_dir = os.path.split(file_name)[0]

        if not os.path.isdir(file_dir):
            os.makedirs(file_dir)

        with open(file_name, "w", encoding='utf-8') as fh:
            fh.write(self.get_json_data() )

    def read(self, file_name):
        if not os.path.isfile(file_name):
            return None

        with open(file_name, "r", encoding='utf-8') as fh:
            data = fh.read()
            self.loads(data)

    def is_valid(self):
        if "title" in self._json and "t_likes" in self._json:
            return True
        else:
            return False

    def get_file_name(self):
        if len(self._json) > 0:
            return self._json["_filename"]

    def get_duration(self):
        if len(self._json) > 0:
            return self._json["duration"]

    def get_title(self):
        if len(self._json) > 0:
            return self._json["title"]

    def get_thumbnail(self):
        if len(self._json) > 0:
            return self._json["thumbnail"]

    def get_stretched_ratio(self):
        if len(self._json) > 0:
            return self._json["stretched_ratio"]

    def get_tags(self):
        if len(self._json) > 0:
            return self._json["tags"]

    def get_categories(self):
        if len(self._json) > 0:
            return self._json["categories"]

    def get_channel_name(self):
        if len(self._json) > 0:
            return self._json["channel"]

    def get_channel_url(self):
        if len(self._json) > 0:
            return self._json["channel_url"]

    def get_description(self):
        if len(self._json) > 0:
            return self._json["description"]

    def get_video_length(self):
        if len(self._json) > 0:
            return int(self._json["duration"])

    def get_chapters(self):
        # chapter => end_time, start_time, title
        if len(self._json) > 0:
            if "chapters" in self._json:
                return self._json["chapters"]

    def get_artist(self):
        if len(self._json) > 0:
            return self._json["artist"]

    def get_channel_name(self):
        if len(self._json) > 0:
            return self._json["channel"]

    def get_channel_code(self):
        if len(self._json) > 0:
            return self._json["channel_id"]

    def get_channel_url(self):
        if len(self._json) > 0:
            return self._json["channel_url"]

    def get_view_count(self):
        if len(self._json) > 0:
            #return str(self._json["view_count"])
            return self._json["t_view_count"]

    def get_thumbs_up(self):
        if len(self._json) > 0:
            #return str(self._json["like_count"])
            return self._json["t_likes"]

    def get_thumbs_down(self):
        if len(self._json) > 0:
            return self._json["t_dislikes"]

    def get_rating(self):
        if len(self._json) > 0:
            return self._json["t_rating"]

    def get_upload_date(self):
        if len(self._json) > 0:
            return self._json["upload_date"]

    def add_return_dislike_data(self, rdd):
        self._json["t_likes"] = rdd.get_likes()
        self._json["t_dislikes"] = rdd.get_dislikes()
        self._json["t_view_count"] = rdd.get_view_count()
        self._json["t_rating"] = rdd.get_rating()
