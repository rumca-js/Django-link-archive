from urllib.parse import urlparse
from urllib.parse import parse_qs

from ..webtools import HtmlPage

class YouTubeVideoHandler(object):
    def __init__(self, url=None):
        self.url = YouTubeVideoHandler.input2url(url)
        self.yt_text = None
        self.yt_ob = None
        self.rd_text = None
        self.rd_ob = None

    def get_video_code(self):
        return YouTubeVideoHandler.input2code(self.url)

    def input2url(item):
        code = YouTubeVideoHandler.input2code(item)
        return YouTubeVideoHandler.code2url(code)

    def code2url(code):
        if code:
            return "https://www.youtube.com/watch?v={0}".format(code)

    def input2code(url):
        if not url:
            return

        wh = url.find("youtu.be")
        video_code = None
        if wh >= 0:
            return YouTubeVideoHandler.input2code_youtu_be(url)
        else:
            return YouTubeVideoHandler.input2code_standard(url)

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
        elements = parse_qs(parsed_elements.query)
        if "v" in elements:
            return elements["v"][0]
        else:
            return None

    def get_link_classic(self):
        return "https://www.youtube.com?v={0}".format(self.get_video_code())

    def get_link_mobile(self):
        return "https://www.m.youtube.com?v={0}".format(self.get_video_code())

    def get_link_youtu_be(self):
        return "https://youtu.be/{0}".format(self.get_video_code())

    def get_link_embed(self):
        return "https://www.youtube.com/embed/{0}".format(self.get_video_code())

    def get_link_music(self):
        return "https://music.youtube.com?v={0}".format(self.get_video_code())

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
            from pytz import timezone

            date_string = self.yt_ob.get_date_published()
            date = datetime.strptime(date_string, "%Y%m%d")
            dt = datetime.combine(date, datetime.min.time())
            dt = dt.replace(tzinfo=timezone("UTC"))

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

    def is_live(self):
        if self.yt_ob:
            return self.yt_ob.is_live() or self.yt_ob.was_live()
        return True

    def load_details(self):
        from ..serializers.youtubelinkjson import YouTubeJson

        self.yt_ob = YouTubeJson()

        if self.yt_text and not self.yt_ob.loads(self.yt_text):
            return False

        # from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown

        # self.rd_ob = YouTubeThumbsDown()
        # if self.rd_text and not self.rd_ob.loads(self.rd_text):
        #    return False

        return True

    def download_details_only(self):
        if self.download_details_yt():  # and self.download_details_rd():
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

    def is_valid(self):
        p = HtmlPage(self.url)
        if not p.is_youtube():
            return False

        if self.is_live():
            return False

        return True
