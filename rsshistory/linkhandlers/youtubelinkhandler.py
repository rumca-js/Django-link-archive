

class YouTubeLinkHandler(object):
    def __init__(self, url = None):
        self.url = url
        self.yt_text = None
        self.yt_ob = None
        self.rd_text = None
        self.rd_ob = None
        self.get_details()

    def get_video_code(self):
        return YouTubeLinkHandler.input2code(self.url)

    def input2url(item):
        code = YouTubeLinkHandler.input2code(item)
        return YouTubeLinkHandler.code2url(code)

    def code2url(code):
        return 'https://www.youtube.com/watch?v={0}'.format(code)

    def input2code(url):
        wh = url.find("=")
        if wh == -1:
            wh = url.find("youtu.be")
            if wh == -1:
                video_code = url
            else:
                video_code = url[wh+9:]
        else:
            wh2 = url.find("&")
            if wh2 != -1:
                video_code = url[wh+1:wh2]
            else:
                video_code = url[wh+1:]
        return video_code

    def get_embed_link(self):
        return "https://www.youtube.com/embed/{0}".format(self.get_video_code() )

    def get_frame(self):
        return "<iframe src=\"{0}\" frameborder=\"0\" allowfullscreen class=\"youtube_player_frame\"></iframe>".format(self.get_embed_link())

    def get_description(self):
        if self.yt_ob:
            return self.yt_ob.get_description()

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

    def get_link_url(self):
        if self.yt_ob:
            return self.yt_ob.get_link_url()

    def load_details(self):
        from ..serializers.youtubelinkjson import YouTubeJson
        self.yt_ob = YouTubeJson()

        if self.yt_text and not self.yt_ob.loads(self.yt_text):
            #logging.error("Could not read json for {0}, removing details data".format(self.url))
            return False

        from ..serializers.returnyoutubedislikeapijson import YouTubeThumbsDown
        self.rd_ob = YouTubeThumbsDown()
        if self.rd_text and not self.rd_ob.loads(self.rd_text):
            #logging.error("Could not read json for {0}, removing returndislike api data".format(self.url))
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

    def get_cached_details(self):
        from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache

        # TODO use .get
        d = YouTubeMetaCache.objects.filter(url=self.url)
        r = YouTubeReturnDislikeMetaCache.objects.filter(url=self.url)

        if not d.exists() or not r.exists():
            pass
        else:
            if not d[0].dead:
                self.yt_text = d[0].details_json
            if not r[0].dead:
                self.rd_text = r[0].return_dislike_json

            if not self.load_details():
                logging.error("Could not read json for {0}".format(self.url))

    def has_cached_details(self):
        from ..models import YouTubeMetaCache, YouTubeReturnDislikeMetaCache

        d = YouTubeMetaCache.objects.filter(url=self.url)
        r = YouTubeReturnDislikeMetaCache.objects.filter(url=self.url)

        if not d.exists() or not r.exists():
            return False

        return True

    def get_details(self):
        if self.has_cached_details():
            return self.get_cached_details()
        else:
            # TODO add details to download
            pass
