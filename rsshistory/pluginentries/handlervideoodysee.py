from .defaulturlhandler import DefaultUrlHandler


class OdyseeVideoHandler(DefaultUrlHandler):
    def __init__(self, url=None):
        super().__init__(url)
        self.url = OdyseeVideoHandler.input2url(url)

    def input2url(url):
        pass

    def get_video_code(self):
        pass

    def get_channel_code(self):
        pass

    def get_link_classic(self):
        return "https://odysee.com/{}/{}".format(
            self.get_channel_code(), self.get_video_code()
        )

    def get_link_embed(self):
        return "https://odysee.com/$/embed/{0}".format(self.get_video_code())
