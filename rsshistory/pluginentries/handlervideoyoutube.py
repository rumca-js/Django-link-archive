from urllib.parse import urlparse
from urllib.parse import parse_qs

from ..webtools import HtmlPage
from .defaulturlhandler import DefaultUrlHandler


class YouTubeVideoHandler(DefaultUrlHandler):
    def __init__(self, url=None):
        super().__init__(url)

        self.url = YouTubeVideoHandler.input2url(url)

        self.yt_text = None
        self.yt_ob = None

        self.rd_text = None
        self.rd_ob = None

        self.return_dislike = False
        self.h = None

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
        return "https://www.youtube.com/watch?v={0}".format(self.get_video_code())

    def get_link_mobile(self):
        return "https://www.m.youtube.com/watch?v={0}".format(self.get_video_code())

    def get_link_youtu_be(self):
        return "https://youtu.be/{0}".format(self.get_video_code())

    def get_link_embed(self):
        return "https://www.youtube.com/embed/{0}".format(self.get_video_code())

    def get_link_music(self):
        return "https://music.youtube.com?v={0}".format(self.get_video_code())

    def get_contents(self):
        if self.dead:
            return

        if self.contents:
            return self.contents

        status = False
        if self.download_details():
            if self.load_details():
                status = True
                self.contents = self.yt_text
                return True

        if not status:
            self.dead = True

    def is_valid(self):
        print("Checking if YouTube is valid")
        if not self.h:
            self.h = HtmlPage(self.url)

        if not self.h.is_youtube():
            print("It is invalid:{} - it is not youtube".format(self.url))
            return False

        if not self.h.is_valid():
            print("It is invalid:{} - handle is not valid".format(self.url))
            return False
        # TODO
        #invalid_text = '{"simpleText":"GO TO HOME"}'
        #contents = self.h.get_contents()
        #if contents and contents.find(invalid_text) >= 0:
        #    print("It is invalid:{} - invalid text found".format(self.url))
        #    return False

        live_field = self.h.get_meta_custom_field("itemprop", "isLiveBroadcast")
        if live_field and live_field.lower() == "true":
            print("It is invalid:{} - live".format(self.url))
            return False

        return True

        if self.is_live():
            return False

        return True

    def get_title(self):
        if self.get_contents():
            return self.yt_ob.get_title()

    def get_description(self):
        if self.get_contents():
            return self.yt_ob.get_description()

    def get_date_published(self):
        if self.get_contents():
            return self.yt_ob.get_date_published()

    def get_datetime_published(self):
        if self.get_contents():
            from datetime import date
            from datetime import datetime
            from pytz import timezone

            date_string = self.yt_ob.get_date_published()
            date = datetime.strptime(date_string, "%Y%m%d")
            dt = datetime.combine(date, datetime.min.time())
            dt = dt.replace(tzinfo=timezone("UTC"))

            return dt

    def get_thumbnail(self):
        if self.get_contents():
            return self.yt_ob.get_thumbnail()

    def get_upload_date(self):
        if self.get_contents():
            return self.yt_ob.get_upload_date()

    def get_view_count(self):
        if self.get_contents():
            return self.rd_ob.get_view_count()

    def get_thumbs_up(self):
        if self.get_contents():
            return self.rd_ob.get_thumbs_up()

    def get_thumbs_down(self):
        if self.get_contents():
            return self.rd_ob.get_thumbs_down()

    def get_channel_code(self):
        if self.get_contents():
            return self.yt_ob.get_channel_code()

    def get_channel_feed_url(self):
        if self.get_contents():
            return self.yt_ob.get_channel_feed_url()

    def get_channel_name(self):
        if self.get_contents():
            return self.yt_ob.get_channel_name()

    def get_link_url(self):
        if self.get_contents():
            return self.yt_ob.get_link_url()

    def is_live(self):
        if self.get_contents():
            return self.yt_ob.is_live()
        return True

    def get_artist(self):
        if self.get_contents():
            return self.get_channel_name()

    def get_album(self):
        return None

    def get_json_text(self):
        if self.get_contents():
            return self.yt_ob.get_json_data()

    def get_tags(self):
        if self.get_contents():
            return self.yt_ob.get_tags()

    def get_properties(self):
        if not self.get_contents():
            return {}

        youtube_props = super().get_properties()

        yt_json = self.yt_ob._json

        if yt_json:
            youtube_props["webpage_url"] = yt_json["webpage_url"]
            youtube_props["uploader_url"] = yt_json["uploader_url"]
            youtube_props["channel_id"] = self.yt_ob.get_channel_code()
            youtube_props["channel"] = self.yt_ob.get_channel_name()
            youtube_props["channel_url"] = self.yt_ob.get_channel_url()
            youtube_props["channel_follower_count"] = yt_json["channel_follower_count"]
            youtube_props["view_count"] = self.yt_ob.get_view_count()
            youtube_props["like_count"] = self.yt_ob.get_thumbs_up()
            if "duration_string" in yt_json:
                youtube_props["duration"] = yt_json["duration_string"]

        youtube_props["embed_url"] = self.get_link_embed()
        youtube_props["valid"] = self.is_valid()
        youtube_props["channel_feed_url"] = self.get_channel_feed_url()
        youtube_props["contents"] = self.get_json_text()
        youtube_props["keywords"] = self.get_tags()
        youtube_props["live"] = self.is_live()

        return youtube_props

    def load_details(self):
        from ..serializers.youtubelinkjson import YouTubeJson

        self.yt_ob = YouTubeJson()

        if self.yt_text and not self.yt_ob.loads(self.yt_text):
            return False

        if self.return_dislike:
            from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown

            self.rd_ob = YouTubeThumbsDown()
            if self.rd_text and not self.rd_ob.loads(self.rd_text):
                return False

        return True

    def download_details(self):
        if not self.download_details_youtube():
            return False
        if not self.download_details_return_dislike():
            return False

        return True

    def download_details_youtube(self):
        if self.yt_text is not None:
            return True

        from ..programwrappers import ytdlp

        yt = ytdlp.YTDLP(self.url)
        self.yt_text = yt.download_data()
        if self.yt_text is None:
            return False
        return True

    def download_details_return_dislike(self):
        if not self.return_dislike:
            return True

        if self.rd_text is not None:
            return True

        from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown

        ytr = YouTubeThumbsDown(self)
        self.rd_text = ytr.download_data()
        if self.rd_text is None:
            return False

        return True
