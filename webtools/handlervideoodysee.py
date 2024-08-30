from .defaulturlhandler import DefaultUrlHandler


class OdyseeVideoHandler(DefaultUrlHandler):
    def __init__(self, url=None, contents=None):
        super().__init__(url, contents=contents)
        self.url = OdyseeVideoHandler.input2url(url)

    def is_handled_by(self):
        if not self.url:
            return

        from .url import Url
        protocol_less = Url.get_protololless(self.url)

        if protocol_less.startswith("odysee.com/@"):
            wh1 = protocol_less.find("@")
            wh2 = protocol_less.find("/", wh1 + 1)
            if wh2 >= 0:
                return True

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
