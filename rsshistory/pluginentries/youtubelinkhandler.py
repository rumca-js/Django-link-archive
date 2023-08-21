from urllib.parse import urlparse
from urllib.parse import parse_qs


class YouTubeLinkHandler(object):
    def __init__(self, url=None):
        self.url = YouTubeLinkHandler.input2url(url)
        self.yt_text = None
        self.yt_ob = None
        self.rd_text = None
        self.rd_ob = None

    def get_video_code(self):
        return YouTubeLinkHandler.input2code(self.url)

    def input2url(item):
        code = YouTubeLinkHandler.input2code(item)
        return YouTubeLinkHandler.code2url(code)

    def code2url(code):
        if code:
            return "https://www.youtube.com/watch?v={0}".format(code)

    def input2code(url):
        wh = url.find("youtu.be")
        video_code = None
        if wh >= 0:
            return YouTubeLinkHandler.input2code_youtu_be(url)
        else:
            return YouTubeLinkHandler.input2code_standard(url)

    def input2code_youtu_be(url):
        wh = url.find("youtu.be")

        wh_question = url.find("?", wh)
        if wh_question >= 0:
            video_code = url[wh + 9 : wh_question]
        else:
            video_code = url[wh + 9 :]

        return video_code

    def input2code_standard(url):
        parsed_elements = urlparse(url)
        return parse_qs(parsed_elements.query)["v"][0]

    def get_embed_link(self):
        return "https://www.youtube.com/embed/{0}".format(self.get_video_code())

    def get_frame(self):
        return '<iframe src="{0}" frameborder="0" allowfullscreen class="youtube_player_frame"></iframe>'.format(
            self.get_embed_link()
        )

    def get_title(self):
        if self.yt_ob:
            return self.yt_ob.get_title()

    def get_description(self):
        if self.yt_ob:
            return self.yt_ob.get_description()

    def get_date_published(self):
        if self.yt_ob:
            return self.yt_ob.get_date_published()

    def get_datetime_published(self):
        if self.yt_ob:
            from datetime import date
            from datetime import datetime

            date_string = self.yt_ob.get_date_published()
            date = datetime.strptime(date_string, "%Y%m%d")
            dt = datetime.combine(date, datetime.min.time())
            return dt

    def get_thumbnail(self):
        if self.yt_ob:
            return self.yt_ob.get_thumbnail()

    def get_upload_date(self):
        if self.yt_ob:
            return self.yt_ob.get_upload_date()

    def get_view_count(self):
        if self.rd_ob:
            return self.rd_ob.get_view_count()

    def get_thumbs_up(self):
        if self.rd_ob:
            return self.rd_ob.get_thumbs_up()

    def get_thumbs_down(self):
        if self.rd_ob:
            return self.rd_ob.get_thumbs_down()

    def get_channel_code(self):
        if self.yt_ob:
            return self.yt_ob.get_channel_code()

    def get_channel_feed_url(self):
        if self.yt_ob:
            return self.yt_ob.get_channel_feed_url()

    def get_channel_name(self):
        if self.yt_ob:
            return self.yt_ob.get_channel_name()

    def get_link_url(self):
        if self.yt_ob:
            return self.yt_ob.get_link_url()

    def load_details(self):
        from ..serializers.youtubelinkjson import YouTubeJson

        self.yt_ob = YouTubeJson()

        if self.yt_text and not self.yt_ob.loads(self.yt_text):
            return False

        from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown

        self.rd_ob = YouTubeThumbsDown()
        if self.rd_text and not self.rd_ob.loads(self.rd_text):
            return False

        return True

    def download_details_only(self):
        if self.download_details_yt() and self.download_details_rd():
            return True
        return False

    def download_details(self):
        if self.download_details_only():
            return self.load_details()

    def download_details_yt(self):
        from ..programwrappers import ytdlp

        yt = ytdlp.YTDLP(self.url)
        self.yt_text = yt.download_data()
        if self.yt_text is None:
            return False
        return True

    def download_details_rd(self):
        from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown

        ytr = YouTubeThumbsDown(self)
        self.rd_text = ytr.download_data()
        if self.rd_text is None:
            return False
        return True
